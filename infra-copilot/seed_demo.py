"""Seed a demo tenant with incidents + a runbook, then run a Copilot query.

Usage (server must be running on :8000):
    python seed_demo.py
"""
from __future__ import annotations

import httpx

BASE = "http://localhost:8000"


def main() -> None:
    with httpx.Client(base_url=BASE, timeout=10) as c:
        tid = c.post("/api/v1/tenants", json={
            "tenant_code": "demo-co", "name": "Demo Co", "plan_code": "enterprise",
        }).json()["id"]
        h = {"X-Tenant-Id": tid, "X-User-Id": "ankit"}

        c.post("/api/v1/incidents", headers=h, json={
            "external_id": "INC1001",
            "title": "Payment API timeout after DB patch",
            "description": "500 errors on payment authorization after database patch.",
            "severity": "P1", "service_name": "Payments API",
            "resolution": "Rolled back DB patch, restarted queue manager.",
        })
        c.post("/api/v1/incidents", headers=h, json={
            "external_id": "INC1002",
            "title": "Payment API 500 during authorization",
            "description": "Latency spike then 500s on payment auth endpoint.",
            "severity": "P1", "service_name": "Payments API",
        })
        c.post("/api/v1/knowledge/documents", headers=h, json={
            "title": "Payments API recovery runbook",
            "source_type": "runbook",
            "content": "On payment 500 errors: check recent DB patches, restart the "
                       "queue manager, validate header flows, reprocess hung transactions.",
        })

        chat = c.post("/api/v1/copilot/chat", headers=h, json={
            "message": "Why is the Payment API returning 500 errors and what should I do?",
        }).json()

        print(f"Tenant: {tid}")
        print(f"Intent: {chat['intent']}  Confidence: {chat['confidence_score']}")
        print("\nAnswer:\n" + chat["answer"])
        print(f"\nProvider: {chat['usage']['provider']} ({chat['usage']['model']})")
        print(f"Citations: {len(chat['citations'])}")


if __name__ == "__main__":
    main()
