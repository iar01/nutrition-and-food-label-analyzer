# LabelLens: Production Operations Runbook

*Operational manual, failure recovery, key rotation, and deployment guide for LabelLens.*

---

## 1. System Topology & Architecture

LabelLens is composed of decoupled microservices and stateless runners designed to fit within free-tier cloud quotas or run locally with Docker Compose:

```
                                  [ Internet / Browser ]
                                             │
                       ┌─────────────────────┴────────────────────┐
                       │                                          │
                  (Port 3000)                                (Port 8000)
             Next.js Frontend (Vercel)                  FastAPI Gateway
             • Zero personal health data                • Auth token validation
             • Client-side profile store                • Rate limiter & concurrency slots
             • ZXing barcode camera                     • Server-Sent Events (SSE)
                       │                                          │
                       └────────── Authenticated Proxy ───────────┘
                                   (X-API-Key: Header)
                                             │
                       ┌─────────────────────┼────────────────────┐
                       │                     │                    │
                  (Port 8765)           (Port 6333)          (Port 5432)
               FastMCP Server        Qdrant Vector DB       PostgreSQL 16
               • Read-only tools     • Hybrid Dense + BM25  • Exact barcode lookup
               • Resource cards      • OpenCLIP packaging   • Full-text trigram index
               • External clients    • Scalar quantization  • Alembic schema
```

---

## 2. Quick Operations Commands

### 2.1 Starting Services in Production
```bash
# Launch entire multi-service production stack
docker compose -f docker-compose.prod.yml up -d --build

# Verify health status of all containers
docker compose -f docker-compose.prod.yml ps
```

### 2.2 Graceful Restart
```bash
# Restart API and Web services without dropping databases
docker compose -f docker-compose.prod.yml restart api web

# Restart vector database
docker compose -f docker-compose.prod.yml restart qdrant
```

### 2.3 Tail Structured Logs
```bash
# Follow JSON logs with request IDs
docker compose -f docker-compose.prod.yml logs -f --tail=100 api

# Filter logs for errors only (PowerShell)
docker compose -f docker-compose.prod.yml logs api | Select-String '"level": "ERROR"'
```

---

## 3. Cold Start & Worker Warmup Handling

### The Cold Start Problem
On initial boot, the FastAPI gateway and agent runtime load pre-trained PyTorch/ONNX models into RAM:
1. **Dense Text Model:** `BAAI/bge-small-en-v1.5` (~130 MB)
2. **Lexical Sparse Model:** `FastEmbed BM25` (~50 MB)
3. **Cross-Encoder Reranker:** `BAAI/bge-reranker-base` (~450 MB)

Model warmup requires **15 to 25 seconds** during which the service cannot answer inference queries.

### UI & Gateway Mitigation
1. **Docker Healthchecks:** The API container definition in `docker-compose.prod.yml` specifies `start_period: 25s`. The Docker ingress router will not route traffic to the container until `/health` returns HTTP 200.
2. **Readiness Probe (`GET /ready`):** Returns HTTP 503 while database connection pools or model caches are initializing.
3. **Frontend Progressive Indicators:** The Next.js frontend emits streaming event steps (`"identifying"`, `"checking_additives"`, `"evaluating_diets"`) with animated skeleton pulse bars. If a 502/503 occurs during cold start, the UI displays an auto-retry countdown banner.

---

## 4. Disaster Recovery & Re-Indexing

### 4.1 Re-creating Qdrant Vector Collections
If the Qdrant volume is corrupted or empty:
```bash
# Step 1: Re-create collections and vector configuration
uv run python scripts/setup_qdrant.py

# Step 2: Index clean products (Dense BGE + Sparse BM25)
uv run python scripts/index_products.py

# Step 3: Index additive and dietary knowledge cards
uv run python scripts/index_knowledge.py

# Step 4: Run retrieval validation
uv run python -m evals.runner --fast
```

### 4.2 Database Migrations (PostgreSQL)
When deploying a new schema version:
```bash
# Apply pending Alembic migrations
uv run alembic upgrade head

# Roll back the previous migration
uv run alembic downgrade -1
```

---

## 5. Zero-Downtime API Key Rotation

LabelLens supports comma-separated keys in `API_KEYS`, allowing zero-downtime key rotation:

1. **Generate New Key:**
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```
2. **Append to Backend `.env`:**
   Update `API_KEYS` to include both the old and new keys:
   ```ini
   API_KEYS=OLD_KEY_STRING,NEW_KEY_STRING
   ```
3. **Reload Backend Workers:**
   ```bash
   docker compose -f docker-compose.prod.yml kill -s SIGHUP api
   # or restart
   docker compose -f docker-compose.prod.yml restart api
   ```
4. **Update Frontend Client:**
   In `apps/web/.env.local` (or Vercel environment variables):
   ```ini
   LABELLENS_API_KEY=NEW_KEY_STRING
   ```
   Deploy the updated frontend.
5. **Retire Old Key:**
   Remove `OLD_KEY_STRING` from the backend `API_KEYS` and reload the backend.

---

## 6. Single Component Failure Analysis

| Failing Component | Symptoms | Automated Fallback Behavior | Operational Remediation |
|---|---|---|---|
| **PostgreSQL** | API `/ready` probe returns 503; exact barcode lookup fails. | System falls back to interim DuckDB database on disk for product reads. | Restart container: `docker compose restart postgres`. Check disk space. |
| **Qdrant Vector DB** | Hybrid search fails; `/ready` returns 503. | `Searcher` automatically falls back to SQL keyword search over DuckDB products. | Restart Qdrant: `docker compose restart qdrant`. If out of memory, enable scalar quantization. |
| **LLM Provider (Ollama / Cloud)** | Analysis synthesis times out (>60s) or fails. | Synthesizer falls back to deterministic rule template (`fallback_summary`). Verdicts are never blocked. | Inspect LLM logs. Check provider quotas or switch `LLM_BASE_URL` to backup provider. |
| **Next.js Web Frontend** | 502 Bad Gateway from reverse proxy. | Static assets served from Vercel edge CDN. Error boundary renders on dynamic pages. | Verify Node process: `docker logs labellens-web-prod`. |

---

## 7. Rollback Procedure & Tagging

LabelLens images follow Semantic Versioning with Git SHA tags:
- `ghcr.io/iar01/labellens-api:v1.0.0`
- `ghcr.io/iar01/labellens-api:sha-4b55a3b`
- `ghcr.io/iar01/labellens-api:latest`

### Instant Rollback via Docker Compose
To roll back to a previously known stable image:
```bash
# Pin image to previous release tag in docker-compose.prod.yml:
# image: ghcr.io/iar01/labellens-api:v1.0.0

docker compose -f docker-compose.prod.yml up -d
```

### Git Rollback
```bash
git checkout <previous_stable_commit>
git checkout -b hotfix-rollback
git push origin hotfix-rollback
```

---

## 8. Free-Tier Deployment Capacity Arithmetic

Can this system run 100% free? **Yes.**

| Service | Recommended Free Provider | Free Limit | LabelLens Footprint |
|---|---|---|---|
| **Frontend** | Vercel Hobby / Cloudflare Pages | 100 GB bandwidth / mo | ~2 MB initial bundle, edge cached |
| **PostgreSQL** | Supabase or Neon Free Tier | 500 MB storage | ~120 MB for 196k product subset |
| **Vector DB** | Qdrant Cloud Free Tier | 1 GB cluster (1M vectors) | ~360 MB for 196k items with INT8 quantization |
| **API Container** | Hugging Face Spaces (Docker) | 2 vCPU, 16 GB RAM (Free) | Uses ~1.8 GB RAM during inference |
| **LLM Inference** | Ollama (local) or Groq / OpenRouter Free | Free models (e.g. Qwen 2.5 7B, Llama 3.3) | Provider-agnostic OpenAI client interface |
