# LabelLens v1.0.0 — Production Release

> **LabelLens** is an open-source, multimodal food label and nutrition analysis platform. It identifies packaged food products via barcode scans, ingredient list photos, or text search; extracts and explains additives and E-numbers with grounded evidence; verifies strict dietary and allergen constraints using deterministic rule engines; orchestrates multi-agent reasoning through LangGraph; and surfaces capabilities via a mobile-first Next.js web application and standard Model Context Protocol (MCP) tools.

---

## 🌟 What's New in v1.0.0

This milestone release marks the completion of all 11 planned architectural phases (Phase 0 through Phase 11), delivering a battle-tested, fully containerized system ready for local development or free-tier cloud deployment.

### 1. Multimodal Hybrid Retrieval (Qdrant + FastEmbed + OpenCLIP)
- **Dense Semantic Embeddings:** 384-dimensional dense vectors using `BAAI/bge-small-en-v1.5` via `sentence-transformers`.
- **Sparse Lexical Embeddings:** BM25 inverted lexical representations via `FastEmbed` for keyword and brand precision.
- **Visual Packaging Embeddings:** 512-dimensional packaging image vectors using OpenCLIP `ViT-B-32` (`openai` weights).
- **Reciprocal Rank Fusion (RRF):** Fuses dense semantic and sparse lexical query scores with parameter $k=60$.
- **Cross-Encoder Reranker:** High-precision neural reranking using `BAAI/bge-reranker-base` to achieve **Recall@5 of 80.8%** and **MRR of 0.736**.

### 2. Deterministic Safety & Rule Engines
- **Zero-Guessing Allergen & Diet Verdicts:** Allergens and diets are evaluated strictly against parsed ingredient tags and standardized knowledge cards—never inferred probabilistically by an LLM.
- **Safety Invariant Enforced:** Guaranteed **0 unsafe false positives** (a product containing an allergen is never marked safe).
- **Trace Contamination & Origin Transparency:** Precautionary cross-contamination warnings (`may contain traces of...`) and ambiguous additive origins (e.g. E322 lecithin from unspecified sources) strictly evaluate to `unknown` with clear advisory warnings.

### 3. Stateful Multi-Agent Orchestration (LangGraph)
- **Structured Routing:** Classifies user intent into barcode, text, photo, compare, alternatives, or general Q&A.
- **Parallel Domain Analysts:** Concurrent execution of Ingredient Analyst, Additive Analyst, and Diet Checker.
- **Human-in-the-Loop Disambiguation:** Halts execution and emits a `choose_product` event when multiple candidates match, allowing the user to select the exact product before resuming.
- **Bounded Revision Critic:** Validates generated claims against source data and strictly blocks ungrounded health assertions or medical advice.

### 4. FastMCP Server (Claude Desktop & External Agents)
- Exposes **10 tools**, **2 resources**, and **2 prompts** implementing the official Model Context Protocol.
- Supports both local **stdio** (zero-overhead execution) and remote **streamable HTTP SSE** (`port 8765`).
- Enables Claude Desktop, Cursor, or any MCP client to perform live barcode lookups, product searches, additive analyses, and dietary fit audits.

### 5. High-Performance API Gateway (FastAPI)
- **Async I/O Architecture:** Built on FastAPI 0.143+ and Uvicorn with Pydantic v2 strict schemas.
- **Server-Sent Events (SSE):** Streaming `/v1/chat` endpoint broadcasting real-time graph progress (`step`, `choose_product`, `final`, `done`).
- **Security & Rate Limiting:** Constant-time `X-API-Key` token validation, sliding-window rate limiting, and CORS allow-lists.

### 6. Mobile-First Web Application (Next.js 16)
- **In-Browser Barcode Scanning:** Real-time camera barcode detection via `@zxing/browser` with GS1 checksum validation.
- **Privacy-First Local Storage:** User allergen and dietary profiles reside exclusively in the client's `localStorage`—no personal health data is stored on backend servers.
- **Adaptive UI:** Responsive layout built with Tailwind CSS v4 and Base UI, featuring clear visual hierarchies for uncertain/unknown verdicts.

### 7. Formal Continuous Evaluation Suite (Phase 10)
- **Automated Regression Gate:** Continuous test harness ([`evals/runner.py`](evals/runner.py)) evaluating retrieval recall, deterministic rule accuracy, and agent scenario success.
- **Golden Sets:** Curated benchmark datasets for allergens ([`evals/golden_rules_set.json`](evals/golden_rules_set.json)) and agent workflows ([`evals/agent_scenarios.json`](evals/agent_scenarios.json)).
- **`make eval` / `make eval-fast`:** Integrated into GitHub Actions CI pipeline.

### 8. Production Hardening & Deployment (Phase 11)
- **Multi-Stage Containerization:** Small, non-root container images for API ([`Dockerfile.api`](Dockerfile.api)), MCP ([`Dockerfile.mcp`](Dockerfile.mcp)), and Web ([`apps/web/Dockerfile`](apps/web/Dockerfile)).
- **Production Compose:** Preconfigured stack ([`docker-compose.prod.yml`](docker-compose.prod.yml)) with explicit resource limits, persistent volumes, and healthchecks.
- **Automated CI/CD:** GitHub Actions workflow ([`.github/workflows/deploy.yml`](.github/workflows/deploy.yml)) building and pushing multi-arch images to GitHub Container Registry (GHCR).
- **Operations Runbook:** Comprehensive guide ([`docs/runbook.md`](docs/runbook.md)) covering cold starts, secret key rotation, re-indexing, and rollbacks.

---

## 📊 Measured Benchmark Results

*Recorded on commit `4b55a3bd` using verified golden datasets:*

| Evaluation Tier | Metric | Target Invariant | Measured Result | Status |
|---|---|---|:---:|:---:|
| **Allergen Detection** | Ground Truth Agreement | 100% | **100.0%** | **PASS** |
| **Diet Safety Invariant** | Unsafe False Positives for 'Safe' | Strictly 0 | **0** | **PASS** |
| **Agent Routing** | End-to-End Task Success Rate | >= 90% | **100.0%** | **PASS** |
| **Medical Safety** | Refusal of Medical / Diagnostic Queries | 100% | **100.0%** | **PASS** |
| **Hybrid Retrieval** | Recall@5 (Hybrid RRF + Cross-Encoder) | >= 80% | **80.8%** | **PASS** |
| **Ranking Precision** | Mean Reciprocal Rank (MRR) | >= 0.70 | **0.736** | **PASS** |

---

## 🚀 Quick Start Guide

### 1. Local Development (uv + Node)
```bash
# Clone the repository
git clone https://github.com/iar01/nutrition-and-food-label-analyzer.git
cd nutrition-and-food-label-analyzer

# Install backend dependencies
uv venv --python 3.12 .venv
source .venv/bin/activate  # Or .venv\Scripts\activate on Windows
uv pip install -e ".[dev]"

# Install frontend dependencies
cd apps/web && npm install && cd ../..

# Configure environment files
cp .env.example .env
# Set API_KEYS in .env and LABELLENS_API_KEY in apps/web/.env.local

# Run fast evaluations
make eval-fast
```

### 2. Production Docker Deployment
```bash
# Launch full multi-container stack in background
docker compose -f docker-compose.prod.yml up -d

# Verify service health
docker compose -f docker-compose.prod.yml ps

# Open in browser: http://localhost:3000
```

---

## 🔒 Security & Privacy

- **No Server-Side Health Profiles:** All dietary restrictions and allergen preferences are stored in the user's browser `localStorage` and sent transiently per request.
- **Zero EXIF Leakage:** Uploaded images are preprocessed on client-side HTML5 Canvas, completely stripping location and device metadata before transmission.
- **Non-Root Containers:** All service containers run as dedicated unprivileged users (`appuser` UID 10001, `mcpuser` UID 10002, `nextjs` UID 1001).

---

## 📚 Acknowledgments & Attribution

- **Data Source:** Nutrition facts, ingredients, and packaging imagery are sourced from [Open Food Facts](https://world.openfoodfacts.org/) under the [Open Database License (ODbL)](https://opendatacommons.org/licenses/odbl/1-0/) and CC BY-SA.
- **Medical Disclaimer:** LabelLens is designed for informational purposes only. It is not a clinical medical device or medical diagnostic tool.
