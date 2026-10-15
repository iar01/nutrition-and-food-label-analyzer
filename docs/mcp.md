# LabelLens Model Context Protocol (MCP) Server

The **LabelLens MCP Server** exposes nutrition, allergen, additive, and food product intelligence behind standard Model Context Protocol (MCP) interfaces. Any MCP-compliant client—such as Claude Desktop, the MCP Inspector, LangGraph agents, or external applications—can invoke deterministic domain tools, attach product/additive resources as context, and use specialized inspection prompts.

---

## 1. Architecture Overview

```
                      +-------------------------------+
 MCP Inspector  ----> |                               |
 Claude Desktop ----> |     LabelLens MCP Server      | ---> DuckDB (Products, Read-Only)
 LangGraph Agent ---> |   (FastMCP, No LLM Inside)    | ---> Qdrant (Dense/Hybrid Embeddings)
 Web App Client ----> |   10 Tools, 2 Resources,      | ---> Additives Knowledge Cards (YAML)
                      |   2 Prompts                   |
                      +-------------------------------+
        stdio (local)  or  Streamable HTTP + Bearer Token (remote)
```

### Architectural Principles

1. **Deterministic Execution (No LLM Inside Server):** All server tools are strictly deterministic (calculating verdicts, querying databases, filtering, or scoring). The *client* provides the LLM. This guarantees reproducible, testable, low-latency, and cost-effective execution.
2. **Schema-as-a-Prompt:** Tool parameter types (`Barcode`, `Literal` enums, string bounds) and detailed docstrings serve as instructions to LLMs for tool selection and argument generation.
3. **Data is Untrusted:** Product text, names, and ingredient strings come from crowd-sourced sources (Open Food Facts). The server treats all string fields as untrusted payload data, preventing prompt injection.
4. **Least Privilege:** Strict read-only database connections, validated inputs, payload size limits, in-memory rate limiting, and zero arbitrary filesystem/shell access.

---

## 2. Tools Reference

### Core Tools

| Tool | Purpose | Inputs | Example Call | Error Format |
|---|---|---|---|---|
| `lookup_by_barcode` | Retrieve the complete record of a single product | `code: str` (8–14 digits, regex validated) | `lookup_by_barcode(code="5000183501108")` | `{"found": false, "error": "not_found", "code": "..."}` |
| `search_products` | Search food products by name, category, or brand with nutritional/diet filters | `query: str` (2–200 chars), `limit: int` (1–10), `diets: list[Diet]`, `exclude_allergens: list[Allergen]`, `nutriscore_in: list[Grade]`, `category: str` | `search_products(query="hazelnut spread", diets=["vegan"], limit=5)` | `{"count": 0, "results": []}` |
| `search_knowledge` | Semantic search over explanation cards (diet rules, label rules, nutrition concepts) | `query: str` (2–200 chars), `k: int` (1–5), `exclude_types: list[str]` | `search_knowledge(query="hidden animal ingredients", k=3)` | `{"count": 0, "results": []}` |
| `get_nutrition` | Retrieve nutrition per 100 g with UK FSA traffic-light levels (low, medium, high) | `code: str` (8–14 digits) | `get_nutrition(code="5000183501108")` | `{"found": false, "error": "not_found", "code": "..."}` |
| `explain_additive` | Plain-language explanation of an E-number or additive with vegan suitability | `identifier: str` (2–80 chars, e.g. "E322" or "lecithin") | `explain_additive(identifier="E322")` | `{"found": false, "error": "no_card", "suggestions": [...]}` |
| `check_diet_fit` | Evaluates product against diets, allergens, and goals using deterministic rules | `code: str`, `diets: list[Diet]`, `allergens: list[Allergen]`, `goals: list[Goal]` | `check_diet_fit(code="5000183501108", diets=["vegan"], allergens=["milk"])` | `{"found": false, "error": "not_found", "code": "..."}` |
| `find_alternatives` | Finds better Nutri-Score alternatives in the same category fitting diet/allergen profile | `code: str`, `diets: list[Diet]`, `allergens: list[Allergen]`, `limit: int` (1–5) | `find_alternatives(code="5000183501108", diets=["vegetarian"], limit=3)` | `{"found": false, "error": "not_found", "code": "..."}` or `{"alternatives": []}` |
| `compare_products` | Side-by-side comparison of 2–4 products on Nutri-Score, NOVA group, and traffic lights | `codes: list[str]` (2 to 4 barcodes) | `compare_products(codes=["5000183501108", "5013092009764"])` | Missing barcodes returned in `"missing"` list |

### Multimodal & Vision Tools (Optional Image / OCR)

| Tool | Purpose | Inputs | Guardrails |
|---|---|---|---|
| `search_by_image` | Reverse-image visual product search using CLIP ViT embeddings | `image_base64: str` (Base64 JPEG/PNG, max 5.5MB chars), `limit: int` (1–10) | 4 MB raw byte limit, Pillow decompression bomb defense (`MAX_IMAGE_PIXELS = 25M`), error `invalid_base64` or `image_too_large` |
| `ocr_label` | OCR packaging text with EasyOCR and regex extraction of candidate barcode numbers | `image_base64: str` (Base64 JPEG/PNG, max 5.5MB chars) | 4 MB raw byte limit, extracts candidate barcodes (8–14 digits) for verification |

---

## 3. Resources

MCP resources provide static or contextual reference data that clients can attach directly into model conversation context:

| URI | MIME Type | Description |
|---|---|---|
| `product://{code}` | `application/json` | Complete product record (ingredients, nutrition per 100g, Nutri-Score, NOVA, tags) for attaching context without tool calls. |
| `additive://{key}` | `application/json` | Additive explanation card (E-number, name, category, vegan status, function, regulatory notes). |

---

## 4. Prompts

MCP prompts provide standardized interactive templates for client interactions:

### `analyze_label`
- **Parameters:** `product: str`, `diets: str = ""`, `allergens: str = ""`
- **Description:** Guided multi-step prompt instructing the client LLM to resolve product identity, look up barcode data, run `check_diet_fit`, explain listed additives, evaluate nutrition traffic lights, and advise caution when information is unknown.

### `diet_audit`
- **Parameters:** `code: str`, `diets: str`, `allergens: str = ""`
- **Description:** Rapid, concise audit prompt instructing the model to call `check_diet_fit` and produce a line-by-line verdict table without speculation.

---

## 5. Real Example: `check_diet_fit` Output

Calling `check_diet_fit(code="5000183501108", diets=["vegan"], allergens=["milk"])` yields:

```json
{
  "found": true,
  "code": "5000183501108",
  "name": "Milk Chocolate spread",
  "verdicts": {
    "diets": {
      "vegan": {
        "status": "not_suitable",
        "reasons": [
          "Product contains allergens: en:milk",
          "Open Food Facts flag indicates diet_vegan = no"
        ]
      }
    },
    "allergens": {
      "milk": {
        "status": "contains",
        "reasons": [
          "Listed in allergens: en:milk",
          "Ingredient match: dried skimmed milk"
        ]
      }
    },
    "goals": {},
    "overall": "not_suitable"
  }
}
```

> **Safety Notice:** The `overall` field is never set to `"safe"`. In the absence of identified conflicts, the system reports `"no_conflicts_found"`, explicitly reminding users to verify the physical packaging.

---

## 6. Transports & How to Run

### Stdio Transport (Local CLI & Claude Desktop)

In `stdio` mode, the server communicates with parent processes via standard input and standard output. All internal logs are directed strictly to `sys.stderr` to prevent JSON-RPC framing corruption.

Run directly:
```powershell
uv run python apps/mcp_server/run.py --transport stdio
```

Inspect using MCP Inspector:
```powershell
npx @modelcontextprotocol/inspector uv run python apps/mcp_server/run.py
```

### Streamable HTTP Transport (Remote & Network Services)

For network access, FastMCP is mounted in an ASGI server behind an `AuthAndRateLimit` middleware:

1. Generate an authentication token:
   ```powershell
   uv run python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```
2. Configure `.env`:
   ```env
   MCP_AUTH_TOKEN=<your-token>
   MCP_URL=http://127.0.0.1:8765/mcp
   ```
3. Launch the HTTP server:
   ```powershell
   uv run python apps/mcp_server/run.py --transport http --port 8765
   ```
4. Test connectivity via smoke test:
   ```powershell
   uv run python scripts/mcp_smoke.py
   ```

---

## 7. Claude Desktop Integration

To register LabelLens in Claude Desktop:

1. Open `%APPDATA%\Claude\claude_desktop_config.json`
2. Add the `labellens` configuration under `mcpServers`:

```json
{
  "mcpServers": {
    "labellens": {
      "command": "C:\\Users\\Abdullah\\.local\\bin\\uv.exe",
      "args": [
        "--directory", "E:\\nutrition-and-food-label-analyzer",
        "run", "python", "apps/mcp_server/run.py"
      ],
      "env": {
        "PYTHONPATH": "E:\\nutrition-and-food-label-analyzer\\packages"
      }
    }
  }
}
```

3. Ensure Qdrant is running (`docker compose up -d`), then fully restart Claude Desktop.

---

## 8. Security & Defenses

| Threat / Risk | Server Defense | Implementation |
|---|---|---|
| **Data Poisoning / Prompt Injection** | Crowd-sourced text is treated purely as untrusted data. Rule evaluations are computed in deterministic Python code, never delegated to model inference. | [`compute_verdicts`](file:///e:/nutrition-and-food-label-analyzer/packages/labellens/agents/rules.py) |
| **State Tampering / Mutation** | Read-only database access; tools tagged with `readOnlyHint=True`. | [`ProductRepo`](file:///e:/nutrition-and-food-label-analyzer/packages/labellens/tools/products.py), `READ_ONLY` hint |
| **Schema Invalidation / Malformed Input** | Strict Pydantic parameter boundaries: 8–14 digit barcode regex, `Literal` enums, string min/max length constraints. | [`packages/labellens/mcp_server/server.py`](file:///e:/nutrition-and-food-label-analyzer/packages/labellens/mcp_server/server.py) |
| **Denial of Service / Memory Attacks** | Image inputs bounded to 4 MB raw buffer, 5.5M base64 chars, and 25 MP Pillow decompression bomb limit. | `decode_image` in [`server.py`](file:///e:/nutrition-and-food-label-analyzer/packages/labellens/mcp_server/server.py) |
| **Path Traversal / Local File Leak** | Zero file-path arguments accepted across all endpoints. Image data is received only as in-memory base64 payloads. | Tool parameter contracts |
| **Unauthorized Network Access** | Mandatory `Authorization: Bearer <token>` verified using constant-time comparison (`hmac.compare_digest`). Local dev `--no-auth` allowed only on `127.0.0.1`/`localhost`. | [`AuthAndRateLimit`](file:///e:/nutrition-and-food-label-analyzer/packages/labellens/mcp_server/http.py) |
| **API Abuse & Flooding** | Per-caller sliding-window rate limiter configured to 120 requests/minute. | [`AuthAndRateLimit`](file:///e:/nutrition-and-food-label-analyzer/packages/labellens/mcp_server/http.py) |
| **Protocol Stream Corruption** | `logging` routed exclusively to `sys.stderr`; zero `print()` statements in server logic. | [`packages/labellens/mcp_server/server.py`](file:///e:/nutrition-and-food-label-analyzer/packages/labellens/mcp_server/server.py) |
