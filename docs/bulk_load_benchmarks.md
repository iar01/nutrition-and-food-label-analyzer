# PostgreSQL Bulk Load Benchmark Report (Phase 3)

Benchmark comparison between **Batched SQLAlchemy INSERT** and **PostgreSQL COPY** on 5,000 records.

---

## Benchmark Results

| Ingestion Method | Batch Size | Duration (s) | Throughput (rows/sec) | Relative Speedup |
|---|---|---|---|---|
| **Batched SQLAlchemy INSERT** | 1,000 | 9.321s | 536.4 rows/s | 1.0x (Baseline) |
| **PostgreSQL COPY (psycopg)** | Streaming | 0.471s | 10,618.2 rows/s | **19.8x Faster** |

---

## Architectural Analysis

* **Why COPY is vastly superior:** The PostgreSQL `COPY` protocol operates directly over the server connection stream without generating parameterized SQL statement ASTs, eliminating statement parsing, query planning overhead, and individual round-trip acknowledgments.
* **Production Decision:** All full-dataset ingestion for LabelLens uses the streaming `COPY` protocol.
