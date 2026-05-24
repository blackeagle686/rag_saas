# RAG-as-a-Service — Full Build Plan
**Author:** Mohammed Alaa  
**Version:** 1.0  
**Date:** May 2026

---

## Vision

A hosted REST API that lets any developer or company add intelligent document search and Q&A to their product in minutes — without managing vector databases, embedding models, or chunking pipelines.

---

## Tech Stack

| Layer | Choice | Why |
|---|---|---|
| API Framework | FastAPI (Python) | You already know it. Async, fast, auto-docs |
| Embedding Model | OpenAI text-embedding-3-small | Best cost/quality ratio |
| Vector DB | Qdrant (self-hosted → managed) | You have experience, great filtering |
| Relational DB | PostgreSQL (via SQLAlchemy) | Tenants, API keys, billing metadata |
| Cache / Rate Limit | Redis | Fast key-value, token bucket rate limiting |
| LLM Layer | Claude Sonnet / GPT-4o (switchable) | Pluggable, model-agnostic design |
| Auth | API Keys (JWT for dashboard) | Simple, developer-friendly |
| Storage | AWS S3 / Cloudflare R2 | Raw file storage before processing |
| Background Jobs | Celery + Redis | Async ingestion pipeline |
| Billing | Stripe Metered Billing | Usage-based, per-query tracking |
| Monitoring | Prometheus + Grafana | Latency, error rates, usage |
| Logging | Loki or CloudWatch | Structured logs per tenant |
| Deployment | Docker + Railway or Render (then AWS) | Fast MVP deploy, cheap |
| CI/CD | GitHub Actions | Auto-test and deploy on push |
| DNS / CDN | Cloudflare | DDoS protection, caching |

---

## Architecture Overview

```
Client App
    │
    ▼
[Cloudflare DNS + WAF]
    │
    ▼
[FastAPI Gateway]  ==== Redis (rate limiting + cache)
    │
    ├== POST /ingest ==► [Celery Worker]
    │                         │
    │                    [S3 Raw Storage]
    │                         │
    │                   [Chunker + Cleaner]
    │                         │
    │                   [Embedder (OpenAI)]
    │                         │
    │                   [Qdrant Vector DB]
    │                         │
    │                   [PostgreSQL metadata]
    │
    └== POST /query ==► [Retriever (Qdrant top-k)]
                              │
                        [Context Builder]
                              │
                        [LLM (Claude / GPT-4o)]
                              │
                        [Response: answer + sources]
```

---

## Task 1 — Project Setup & Repository Structure

- Initialize Git monorepo with the following structure:
  ```
  ragaas/
  ├== api/             # FastAPI app
  ├== workers/         # Celery ingestion workers
  ├== sdk/             # Optional Python SDK (later)
  ├== dashboard/       # React frontend (later)
  ├== infra/           # Docker, docker-compose, Terraform
  ├== scripts/         # Dev utilities
  └== docs/            # API documentation source
  ```
- Set up `pyproject.toml` with dependencies: fastapi, uvicorn, sqlalchemy, asyncpg, celery, redis, qdrant-client, openai, stripe, pydantic, python-jose, passlib, boto3
- Configure `.env` with environment variable schema and `.env.example` for contributors
- Set up pre-commit hooks: black, isort, ruff, mypy
- Create `docker-compose.yml` for local dev: FastAPI + PostgreSQL + Redis + Qdrant
- Configure GitHub Actions: lint → test → build → deploy pipeline

---

## Task 2 — Database Schema & Models

Design PostgreSQL schema for multi-tenancy:

**Table: `tenants`**
```sql
id          UUID PRIMARY KEY
name        TEXT
email       TEXT UNIQUE
plan        TEXT  -- starter | growth | scale | enterprise
created_at  TIMESTAMP
status      TEXT  -- active | suspended | cancelled
```

**Table: `api_keys`**
```sql
id          UUID PRIMARY KEY
tenant_id   UUID FK → tenants
key_hash    TEXT UNIQUE  -- bcrypt hash, never store raw
prefix      TEXT         -- first 8 chars shown in dashboard
created_at  TIMESTAMP
last_used   TIMESTAMP
is_active   BOOLEAN
```

**Table: `namespaces`**
```sql
id           UUID PRIMARY KEY
tenant_id    UUID FK → tenants
name         TEXT
doc_count    INT
token_count  BIGINT
created_at   TIMESTAMP
```

**Table: `documents`**
```sql
id            UUID PRIMARY KEY
namespace_id  UUID FK → namespaces
filename      TEXT
file_type     TEXT
status        TEXT  -- pending | processing | ready | failed
chunk_count   INT
s3_key        TEXT
created_at    TIMESTAMP
```

**Table: `usage_events`**
```sql
id            UUID PRIMARY KEY
tenant_id     UUID FK → tenants
event_type    TEXT  -- query | ingest
tokens_used   INT
query_ms      INT
model_used    TEXT
created_at    TIMESTAMP
```

- Implement SQLAlchemy async models for all tables
- Set up Alembic for database migrations
- Seed script for local dev with test tenant + API key

---

## Task 3 — Authentication & API Key System

- Generate API keys in format: `rgs_live_xxxxxxxxxxxxxxxxxxxxxxxx` (prefix shows environment)
- Store only `bcrypt` hash of the key in database — never the raw key
- Build FastAPI middleware `verify_api_key`:
  - Extract key from `Authorization: Bearer <key>` header
  - Hash incoming key and compare to DB hash
  - Attach `tenant` object to request state
  - Return `401` with clear error if invalid
- Implement key rotation endpoint: `POST /v1/keys/rotate`
- Implement key listing: `GET /v1/keys` (shows prefix + last used, never full key)
- Implement key revocation: `DELETE /v1/keys/{key_id}`
- Rate limiter middleware using Redis token bucket:
  - Starter: 10 req/sec
  - Growth: 50 req/sec
  - Scale: 200 req/sec
  - Return `429 Too Many Requests` with `Retry-After` header

---

## Task 4 — File Ingestion Pipeline

**Endpoint:** `POST /v1/ingest`

Request body:
```json
{
  "namespace": "my-docs",
  "file_url": "https://...",   // OR multipart upload
  "metadata": { "source": "legal-team", "year": 2025 }
}
```

Response:
```json
{
  "document_id": "uuid",
  "status": "processing",
  "estimated_seconds": 15
}
```

Pipeline steps (run as Celery background task):
1. Download file from URL or S3 upload
2. Store raw file in S3 under `{tenant_id}/{namespace_id}/{document_id}`
3. Extract text: PDF via `pdfplumber`, DOCX via `python-docx`, TXT direct, HTML via `BeautifulSoup`
4. Clean text: strip boilerplate, fix encoding, normalize whitespace
5. Chunk text: recursive character splitter, chunk size 512 tokens, 50-token overlap
6. Embed chunks in batches of 100: OpenAI `text-embedding-3-small`
7. Upsert to Qdrant: each point = `{chunk_text, embedding, metadata, document_id, chunk_index}`
8. Update `documents` table: status → `ready`, chunk_count updated
9. Update `namespaces` table: token_count incremented
10. Log usage event to `usage_events`

Supported file types at launch: `.pdf`, `.docx`, `.txt`, `.md`, `.html`

Error handling:
- File too large (>50MB): reject immediately with `413`
- Unsupported type: `415`
- Processing failure: mark document as `failed`, return error webhook if configured

---

## Task 5 — Query Endpoint

**Endpoint:** `POST /v1/query`

Request body:
```json
{
  "namespace": "my-docs",
  "query": "What is our refund policy?",
  "top_k": 5,
  "filters": { "source": "legal-team" },
  "stream": false,
  "model": "claude-sonnet"
}
```

Response:
```json
{
  "answer": "According to your policy...",
  "sources": [
    {
      "document_id": "uuid",
      "filename": "refund-policy.pdf",
      "chunk": "Customers may request refunds within 30 days...",
      "score": 0.94
    }
  ],
  "latency_ms": 380,
  "tokens_used": 1240
}
```

Pipeline:
1. Embed the query using same model as ingestion
2. Query Qdrant: cosine similarity, top-k chunks, apply metadata filters
3. Build context: concatenate retrieved chunks with source labels
4. Call LLM with system prompt: "Answer using only the provided context. If unsure, say so."
5. Parse response, attach source references
6. Log usage event (query type, tokens used, latency, model)
7. Return structured JSON

Optional streaming: use `StreamingResponse` with server-sent events if `stream: true`

---

## Task 6 — Namespace Management API

Endpoints to build:

```
POST   /v1/namespaces              Create a namespace
GET    /v1/namespaces              List all namespaces
GET    /v1/namespaces/{name}       Get stats for a namespace
DELETE /v1/namespaces/{name}       Delete namespace + all vectors + docs
GET    /v1/namespaces/{name}/docs  List documents in namespace
DELETE /v1/documents/{id}          Delete a specific document
```

When a namespace is deleted:
1. Delete all Qdrant points under that namespace
2. Delete all S3 files under that prefix
3. Delete DB records (cascade)
4. This is irreversible — require `confirm: true` in request body

---

## Task 7 — Security Hardening

**Input validation:**
- Pydantic models on all request bodies — never trust raw input
- Max file size: 50MB enforced at upload middleware
- Query max length: 2000 characters
- Namespace name: alphanumeric + dashes only, max 64 chars

**Injection prevention:**
- No raw SQL — SQLAlchemy ORM only with parameterized queries
- Sanitize filenames before S3 storage
- Strip executable content from uploaded files

**Tenant isolation:**
- Every DB query includes `WHERE tenant_id = :current_tenant`
- Every Qdrant query scoped to tenant's namespace collection
- API keys cryptographically tied to tenant — no cross-tenant access possible

**Transport security:**
- HTTPS only — HTTP redirects to HTTPS at Cloudflare level
- TLS 1.2 minimum
- HSTS headers on all responses

**Secrets management:**
- All secrets via environment variables — never in code or Git
- Use AWS Secrets Manager or Doppler in production
- Rotate OpenAI and Stripe keys quarterly

**Audit logging:**
- Log every API key use: timestamp, endpoint, IP, tenant
- Log every document ingestion and deletion
- Retain logs 90 days minimum
- Separate audit log from application log

**DDoS & abuse protection:**
- Cloudflare WAF in front of all traffic
- IP-level rate limiting at Cloudflare (before hitting your server)
- Per-key rate limiting at Redis layer (inside your server)
- Suspicious pattern detection: flag tenants querying >10x normal rate

**Dependency security:**
- `pip-audit` in CI pipeline — fail build on known CVEs
- Dependabot for automated PR on dependency updates
- Pin all dependency versions in `requirements.lock`

---

## Task 8 — Billing Integration (Stripe)

- Set up Stripe Metered Billing product with two meters: `queries` and `ingested_tokens`
- On tenant signup: create Stripe Customer, attach payment method, create Subscription
- After every query: increment Stripe meter via `stripe.billing.meter_events.create`
- After every ingestion: increment ingested_tokens meter
- Implement webhook endpoint `POST /webhooks/stripe`:
  - `invoice.payment_failed` → send email warning, suspend after 3 failures
  - `customer.subscription.deleted` → mark tenant as cancelled, keep data 30 days
  - `customer.subscription.updated` → sync plan changes to DB

Plan limits enforced in middleware:
- Check monthly query count from `usage_events` table
- If over plan limit: return `402 Payment Required` with upgrade message

---

## Task 9 — Monitoring & Observability

**Application metrics (Prometheus):**
- Request latency p50/p95/p99 per endpoint
- Query success rate
- Ingestion queue depth
- LLM call latency
- Qdrant query latency
- Active tenants per plan

**Dashboards (Grafana):**
- Real-time request rate
- Error rate by endpoint
- Usage by tenant (top 10)
- Revenue proxy: queries × rate per plan

**Alerting:**
- Error rate >5% for 5 minutes → PagerDuty / Telegram alert
- Ingestion queue >100 jobs → scale workers
- DB connection pool exhausted → immediate alert
- LLM API error rate >10% → fallback to secondary model

**Structured logging:**
- Every log line includes: `tenant_id`, `request_id`, `endpoint`, `duration_ms`, `status_code`
- Log level: INFO for normal operations, ERROR for failures, WARN for slow queries (>2s)
- Ship logs to Loki or CloudWatch

**Health endpoints:**
```
GET /health          Basic liveness check
GET /health/ready    DB + Redis + Qdrant connectivity check
```

---

## Task 10 — Developer Dashboard (Frontend)

Stack: React + Vite + Tailwind CSS

Pages to build:

**1. Onboarding**
- Signup with email + password
- Email verification
- Credit card entry (Stripe Elements)
- API key shown once on creation (with copy button + warning)

**2. Dashboard Home**
- Queries this month vs limit (progress bar)
- Tokens ingested vs limit
- Last 7 days query chart
- Quick API key display

**3. Namespaces**
- List all namespaces with doc count + token count
- Create namespace form
- Click into namespace → see documents, delete documents

**4. API Keys**
- List keys with prefix + last used
- Create new key (modal with one-time display)
- Revoke key

**5. Usage & Billing**
- Monthly usage breakdown
- Stripe portal link for payment method / invoices
- Plan upgrade/downgrade

**6. Docs**
- Embedded interactive API docs (FastAPI auto-generated Swagger UI)

---

## Task 11 — API Documentation & Developer Experience

- Write complete OpenAPI spec via FastAPI decorators — descriptions, examples, error codes on every endpoint
- Build public docs site using Mintlify or Docusaurus:
  - Quickstart: "From zero to your first query in 5 minutes"
  - Authentication guide
  - Ingestion guide (all file types + limits)
  - Query guide (filters, streaming, model selection)
  - Error reference (every error code with fix instructions)
  - Code examples in Python, JavaScript, cURL for every endpoint
- Publish a Python SDK (`pip install ragaas`): thin wrapper around the REST API with typed responses
- Postman collection exported and linked from docs

---

## Task 12 — Launch & Customer Acquisition

**Week 1 — Beta launch:**
- Post on Hacker News: "Show HN: RAG API — add document search to your app in 10 lines"
- Post on dev.to and Reddit (r/MachineLearning, r/LangChain, r/SideProject, r/webdev)
- Offer 3 months free Growth plan to first 10 beta users
- Personally DM 20 developers who have publicly complained about RAG complexity on Twitter/X

**Week 2 — Target the pain:**
- Search Twitter/X: "langchain too complex", "qdrant setup", "vector database pain"
- Reply with genuine help — don't pitch, just help. Link your tool if relevant
- Join Discord servers: LangChain, LlamaIndex, OpenAI developers
- Offer to help people with RAG problems — become known as the person who solves this

**Week 3 — First case study:**
- Pick most engaged beta user
- Help them deeply — pair program if needed
- Document their before/after: "X cut RAG setup from 3 weeks to 1 day"
- This is your homepage hero section

**Week 4+ — Content engine:**
- LinkedIn: 2 posts per week — tutorials, behind-the-scenes, architecture deep-dives
- Twitter/X: Daily short tips on RAG, embeddings, LLM APIs
- YouTube: 1 video per month — "How I built X" or "RAG tutorial"
- Arabic content: post the same content in Arabic for MENA reach (massive untapped audience)

**Partnerships:**
- Reach out to no-code tools (Bubble, Webflow) — offer a native integration
- Reach out to legal tech, HR tech, and customer support tool founders directly on LinkedIn
- List on AI tool directories: There's An AI For That, Futurepedia, Product Hunt

---

## Task 13 — Roadmap (Post-Launch)

**Phase 2 (Month 2–3):**
- Streaming query responses (SSE)
- Webhook events for ingestion completion
- Metadata filtering on queries
- Support for web URLs as input (scrape + ingest)
- Multi-language support (Arabic first — your competitive edge)

**Phase 3 (Month 4–6):**
- Custom embedding model support (bring your own)
- Hybrid search (vector + BM25 keyword)
- Conversation memory (multi-turn Q&A with context)
- Analytics API: query trends, popular topics
- On-premise / self-hosted enterprise tier

**Phase 4 (Month 7–12):**
- White-label option for agencies
- Fine-tuned domain-specific models (legal, medical, HR)
- SOC 2 Type II certification (required for enterprise sales)
- GDPR-compliant EU data region

---

## Budget Estimate (First 3 Months)

| Item | Monthly Cost |
|---|---|
| Render / Railway (API + workers) | ~$25 |
| Qdrant Cloud (1GB free → $25/mo after) | $0–25 |
| PostgreSQL (Railway managed) | ~$10 |
| Redis (Railway) | ~$5 |
| OpenAI Embeddings (beta usage) | ~$10–30 |
| LLM API calls (Claude / GPT-4o) | ~$20–50 |
| Cloudflare (free tier) | $0 |
| Stripe (no monthly fee, 2.9% per transaction) | $0 until revenue |
| **Total** | **~$70–145/month** |

Your break-even: 2 Growth plan customers ($99 × 2 = $198/mo) covers all infra costs.

---

## Definition of Done — MVP

The MVP is complete when:

- [ ] `POST /v1/ingest` accepts PDF, DOCX, TXT and processes asynchronously
- [ ] `POST /v1/query` returns an answer with source references in <2 seconds
- [ ] API key auth works with per-tenant isolation
- [ ] Rate limiting enforced per plan tier
- [ ] Stripe billing tracks query usage and charges monthly
- [ ] Dashboard shows usage stats and lets users manage namespaces
- [ ] Public docs site live with Quickstart guide
- [ ] Health endpoints return status of all dependencies
- [ ] 10 beta users signed up and querying real data

---

*Built by Mohammed Alaa — AI Infrastructure Engineer*  
*"Make the complex invisible. Give developers one clean API."*