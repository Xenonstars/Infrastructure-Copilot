# Infrastructure Copilot — MVP Reference Implementation

An **AI-powered Incident & Change Intelligence** platform skeleton.
Multi-tenant, BYOK, RAG-grounded, audited — and it runs with **zero API keys**
thanks to a built-in mock model provider.

> This is a **runnable MVP skeleton**, not the full 26-sprint platform.
> It proves the architecture end-to-end so real engineering can start from Sprint 0.

---

## What actually works right now

| Capability | Status |
|---|---|
| Multi-tenant provisioning | ✅ |
| Tenant isolation (Tenant A can't see Tenant B) | ✅ enforced + tested |
| Incident ingest + list + get | ✅ |
| Similar-incident search (lexical similarity) | ✅ |
| Knowledge ingest (runbooks / KBs / SOPs / RCAs) | ✅ |
| RAG retrieval (tenant-scoped, grounded) | ✅ |
| BYOK AI provider registration (secret stored as reference only) | ✅ |
| AI Orchestrator (intent → RAG → model → citations → audit) | ✅ |
| Copilot chat with citations + token usage | ✅ |
| Audit trail per tenant | ✅ |
| Auto OpenAPI docs at `/docs` | ✅ |

## What is deliberately stubbed (see roadmap)

- Real Azure OpenAI / OpenAI calls (interface is ready; mock provider used by default)
- PostgreSQL + Row-Level Security (in-memory store used; swap the `database.py` layer)
- Azure AI Search hybrid/vector retrieval (pure-Python similarity used)
- Entra ID / Okta JWT auth (header-based tenant context used)
- Change intelligence, service graph, connectors, AKS deployment

---

## Run it

```bash
pip install -r requirements.txt

# start the API
uvicorn app.main:app --reload
# open http://localhost:8000/docs

# in another terminal, seed a demo + run a Copilot query
python seed_demo.py
```

### Run the tests

```bash
python -m pytest -q
```

### Docker

```bash
docker build -t infra-copilot .
docker run -p 8000:8000 infra-copilot
```

---

## Architecture mapping

| Spec artifact | Where it lives |
|---|---|
| Domain Model | `app/domain/__init__.py` |
| Data layer (→ PostgreSQL later) | `app/database.py` |
| Tenant isolation | `app/security.py` + `tenant_id` everywhere |
| RAG Architecture | `app/services/rag_service.py` + `similarity.py` |
| BYOK Model Gateway | `app/services/ai_gateway.py` |
| AI Orchestration | `app/services/orchestrator.py` |
| OpenAPI contract | auto-generated at `/docs` and `/openapi.json` |
| Audit / governance | `app/services/audit_service.py` |

---

## Using a real BYOK provider

1. `POST /api/v1/ai-providers` with `provider_type=azure_openai`, `endpoint_url`,
   `default_model`, and `secret_value`. The raw secret is **never stored** — only a
   `kv://...` reference is persisted.
2. Implement `AzureOpenAIProvider.generate()` in `app/services/ai_gateway.py`
   (or add keyless Entra ID auth).
3. That's it — the orchestrator will route to it automatically.

---

## Honest scope note

This is roughly **5% of the full product** — the foundational slice that de-risks
everything else. Next real steps: swap in PostgreSQL + RLS, wire Azure AI Search,
add Entra ID auth, and build the first real connector (ServiceNow).
