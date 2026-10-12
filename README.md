# LabelLens: Nutrition & Food Label Analyzer

> **LabelLens** is an open-source, multimodal, agentic food label and nutrition analysis platform. It identifies products via barcodes, packaging photos, or names, explains additives and ingredients with grounded evidence, verifies strict dietary and allergen constraints with deterministic rule engines, and exposes all capabilities through standard Model Context Protocol (MCP) tools.

---

## 1. Architecture Overview

```text
Next.js UI ──► FastAPI Gateway ──► LangGraph Agent Graph ──► MCP Client
                   │                                            │
                   │                                    MCP Server (FastMCP)
                   │                       ┌───────────────┼────────────────┐
                   ▼                       ▼               ▼                ▼
              Postgres                Qdrant:          Qdrant:          OCR + CLIP
              (products, users,       products         knowledge        (image path)
               profiles)              dense+image+     (additives,
                                      sparse           diet rules)

LLM: OpenAI-compatible endpoint → Ollama (local dev) / free API tier (prod)
```

### Core Design Principles
1. **Deterministic first, LLM second:** Barcode lookups, allergen matching, and diet verdicts are computed with strict SQL and rule engines, never LLM guessing. The LLM only explains and orchestrates.
2. **Provider-agnostic LLM:** Unified OpenAI-compatible interface; model and endpoint configured via environment variables (`LLM_MODEL`, `LLM_BASE_URL`).
3. **Everything through MCP tools:** The same tools serve internal LangGraph agents, the FastAPI gateway, and external MCP clients (such as Claude Desktop).
4. **Privacy-first profile:** Dietary preferences and allergen lists are stored client-side in the browser, not saved on external servers.

---

## 2. Requirements

- **Operating System:** Windows 10/11 (WSL2), Linux, or macOS
- **Python:** 3.12 (managed via `uv`)
- **Docker & Docker Compose:** Docker Engine 24+ / Compose v2
- **Node.js:** 20+ LTS (for Next.js frontend)
- **Local LLM:** Ollama (default: `qwen2.5:7b` or `qwen2.5:3b`)

---

## 3. Quick Start

### 1. Clone & Set Up Python Environment
```bash
# Clone the repository
git clone https://github.com/iar01/nutrition-and-food-label-analyzer.git
cd nutrition-and-food-label-analyzer

# Create virtual environment with Python 3.12 and install dependencies
uv venv --python 3.12 .venv
.venv\Scripts\activate      # On Windows
# source .venv/bin/activate # On Linux/macOS

# Install development package
uv pip install -e ".[dev]"
```

### 2. Configure Environment
```bash
cp .env.example .env
```
Inspect `.env` and verify database, vector store, and LLM connection settings.

### 3. Start Infrastructure (Postgres & Qdrant)
```bash
docker compose up -d
```
Verify container health:
```bash
docker compose ps
```
- PostgreSQL 16: `localhost:5432`
- Qdrant Vector Store: `localhost:6333` (HTTP) / `localhost:6334` (gRPC)

### 4. Run Ollama & LLM Smoke Test
Make sure Ollama is running and has pulled the model:
```bash
ollama run qwen2.5:7b
```
Run the smoke test:
```bash
pytest -m smoke tests/test_smoke_llm.py
```

### 5. Run All Quality Checks
```bash
# Linting & Formatting
ruff check .
ruff format --check .

# Type checking
mypy packages

# Unit tests
pytest -m "not smoke"
```

---

## 4. Project Layout

```text
nutrition-and-food-label-analyzer/
├── apps/
│   ├── api/            # FastAPI gateway
│   ├── mcp_server/     # FastMCP server
│   └── web/            # Next.js frontend
├── packages/labellens/ # Shared Python package
│   ├── config.py       # Pydantic Settings configuration
│   ├── data/           # Extraction, cleaning, DuckDB loader
│   ├── embeddings/     # Text (BGE), Image (CLIP), Sparse (BM25)
│   ├── retrieval/      # Qdrant hybrid retrieval & rerankers
│   ├── agents/         # LangGraph state machine & analyst nodes
│   ├── db/             # SQLAlchemy 2 models & Alembic migrations
│   └── llm/            # OpenAI-compatible provider abstraction
├── data/               # Gitignored data storage: raw/ interim/ clean/ images/
├── notebooks/          # Exploratory data analysis & experiments
├── evals/              # Golden eval sets and metric scripts
├── infra/              # Dockerfiles, CI workflows, deployment manifests
├── docs/               # Data dictionary, design documentation
├── tests/              # Unit, integration, and smoke tests
├── pyproject.toml      # Build and dependency definition (uv)
├── docker-compose.yml  # Local Postgres & Qdrant infrastructure
├── .env.example        # Environment variable template
└── README.md
```

---

## 5. Data & Attribution

- **Source:** Open Food Facts (`openfoodfacts/product-database`)
- **License:** Open Database License (ODbL) for product data; CC BY-SA for packaging images.
- **Attribution:** Data sourced with appreciation from the global Open Food Facts community.

---

## 6. Disclaimer

LabelLens is an educational and informational tool. **It does not provide medical or clinical nutritional advice.** Always consult healthcare professionals for acute dietary and severe allergic conditions.

---

## 7. License

Code is licensed under the [MIT License](LICENSE).
