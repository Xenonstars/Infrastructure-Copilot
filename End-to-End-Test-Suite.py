"""End-to-end MVP tests.

Proves the four things that make this enterprise-credible:
  1. Multi-tenant CRUD works.
  2. Tenant isolation is enforced (Tenant A cannot see Tenant B).
  3. RAG retrieval is grounded and tenant-scoped.
  4. The orchestrator produces cited answers via the BYOK mock provider.
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _new_tenant(code: str, name: str) -> str:
    r = client.post("/api/v1/tenants", json={"tenant_code": code, "name": name})
    assert r.status_code == 201, r.text
    return r.json()["id"]


def _h(tenant_id: str, user: str = "ankit") -> dict:
    return {"X-Tenant-Id": tenant_id, "X-User-Id": user}


def test_health():
    assert client.get("/health").json()["status"] == "ok"


def test_end_to_end_and_tenant_isolation():
    # Two tenants
    t_bank = _new_tenant("abc-bank", "ABC Bank")
    t_retail = _new_tenant("xyz-retail", "XYZ Retail")

    # Seed incidents in the bank tenant
    client.post("/api/v1/incidents", headers=_h(t_bank), json={
        "external_id": "INC1001",
        "title": "Payment API timeout after DB patch",
        "description": "Payment authorization failing with 500 after database patch.",
        "severity": "P1", "service_name": "Payments API",
        "resolution": "Rolled back DB patch, restarted queue manager.",
    })
    inc2 = client.post("/api/v1/incidents", headers=_h(t_bank), json={
        "external_id": "INC1002",
        "title": "Payment API 500 errors during authorization",
        "description": "Latency spike on payment authorization endpoint.",
        "severity": "P1", "service_name": "Payments API",
    }).json()

    # Seed a runbook in the bank tenant
    client.post("/api/v1/knowledge/documents", headers=_h(t_bank), json={
        "title": "Payments API recovery runbook",
        "source_type": "runbook",
        "content": "If payment authorization returns 500, check recent DB patches, "
                   "restart the queue manager, then validate header flows.",
    })

    # Seed an incident in the retail tenant (must NOT leak)
    client.post("/api/v1/incidents", headers=_h(t_retail), json={
        "external_id": "INC9001",
        "title": "Checkout cart service crash",
        "description": "Retail checkout cart failing on peak load.",
        "severity": "P2", "service_name": "Cart Service",
    })

    # --- Tenant isolation: bank sees only its incidents ---
    bank_incidents = client.get("/api/v1/incidents", headers=_h(t_bank)).json()
    assert len(bank_incidents) == 2
    titles = {i["title"] for i in bank_incidents}
    assert all("Cart" not in t for t in titles)

    retail_incidents = client.get("/api/v1/incidents", headers=_h(t_retail)).json()
    assert len(retail_incidents) == 1
    assert retail_incidents[0]["external_id"] == "INC9001"

    # --- Unknown tenant is rejected ---
    assert client.get("/api/v1/incidents", headers=_h("does-not-exist")).status_code == 403

    # --- Similar incidents (tenant-scoped) ---
    similar = client.post(f"/api/v1/incidents/{inc2['id']}/similar", headers=_h(t_bank)).json()
    assert len(similar) >= 1
    assert similar[0]["incident"]["external_id"] == "INC1001"
    assert similar[0]["similarity_score"] > 0

    # --- Copilot chat is grounded + cited (via BYOK mock provider) ---
    chat = client.post("/api/v1/copilot/chat", headers=_h(t_bank), json={
        "message": "Why is the Payment API returning 500 errors?",
    }).json()
    assert chat["citations"], "expected grounded citations"
    assert chat["usage"]["provider"] == "mock"
    assert chat["confidence_score"] > 0
    assert "Payment" in chat["answer"] or "payment" in chat["answer"]

    # --- Copilot for the retail tenant must NOT retrieve bank data ---
    retail_chat = client.post("/api/v1/copilot/chat", headers=_h(t_retail), json={
        "message": "Why is the Payment API returning 500 errors?",
    }).json()
    for c in retail_chat["citations"]:
        assert c["source_id"] not in ("INC1001", "INC1002")

    # --- Audit trail recorded per tenant ---
    audit = client.get("/api/v1/audit/events", headers=_h(t_bank)).json()
    actions = {e["action"] for e in audit}
    assert "incident.create" in actions
    assert "copilot.chat" in actions


def test_byok_provider_stores_only_reference():
    t = _new_tenant("secure-co", "Secure Co")
    r = client.post("/api/v1/ai-providers", headers=_h(t), json={
        "display_name": "Customer Azure OpenAI",
        "provider_type": "azure_openai",
        "auth_mode": "api_key",
        "endpoint_url": "https://customer.openai.azure.com",
        "default_model": "gpt-4o",
        "secret_value": "super-secret-should-never-be-stored",
    })
    assert r.status_code == 201
    body = r.json()
    # Raw secret is never returned or stored; only a vault reference.
    assert "super-secret" not in str(body)
    assert body["secret_reference"].startswith("kv://")
