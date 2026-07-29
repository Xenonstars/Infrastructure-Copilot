"""AI Orchestrator — the decision engine.

Flow (v1, single-agent, read-only, policy-controlled):
  classify intent -> retrieve authorized context (RAG) -> build prompt
  -> call BYOK model gateway -> attach citations -> confidence -> audit.
The LLM never decides alone; the orchestrator decides through policy.
"""
from __future__ import annotations

from app.database import store
from app.domain import CopilotChatRequest, CopilotChatResponse
from app.services import ai_gateway, audit_service, rag_service

INTENT_KEYWORDS = {
    "SIMILAR_INCIDENT_SEARCH": ("similar", "seen before", "happened before", "recurring"),
    "RCA_GENERATION": ("root cause", "rca", "why did", "postmortem", "post mortem"),
    "CHANGE_RISK_ANALYSIS": ("change", "deployment", "release", "risk"),
    "RUNBOOK_RETRIEVAL": ("runbook", "how do i", "steps", "procedure", "restart"),
    "EXECUTIVE_UPDATE": ("update", "stakeholder", "summary", "communicate"),
}


def classify_intent(message: str) -> str:
    m = message.lower()
    for intent, kws in INTENT_KEYWORDS.items():
        if any(k in m for k in kws):
            return intent
    return "INCIDENT_INVESTIGATION"


def _format_prefix(intent: str) -> str:
    return {
        "RCA_GENERATION": "Draft RCA based strictly on the grounded context.",
        "EXECUTIVE_UPDATE": "Write a concise stakeholder update grounded in context.",
        "RUNBOOK_RETRIEVAL": "Provide the most relevant runbook steps from context.",
        "CHANGE_RISK_ANALYSIS": "Assess change risk using the grounded context.",
        "SIMILAR_INCIDENT_SEARCH": "Surface similar past incidents from context.",
        "INCIDENT_INVESTIGATION": "Guide the investigation using grounded context.",
    }.get(intent, "Answer using grounded context.")


def chat(tenant_id: str, user_id: str, req: CopilotChatRequest) -> CopilotChatResponse:
    intent = classify_intent(req.message)

    # Enrich query with incident context if provided (still tenant-scoped).
    query = req.message
    if req.incident_id:
        inc = store.get_incident(tenant_id, req.incident_id)
        if inc:
            query = f"{req.message} {inc.title} {inc.description} {inc.service_name or ''}"

    citations = rag_service.retrieve(tenant_id, query)

    prompt = (
        f"System: You are Infrastructure Copilot. {_format_prefix(intent)} "
        f"Only use the provided context. Cite sources.\n"
        f"User: {req.message}\n"
        f"Context items: {len(citations)}"
    )

    answer, usage = ai_gateway.complete(tenant_id, prompt, citations)

    # Confidence: driven by best retrieval score (no context => low confidence).
    confidence = round(citations[0].relevance_score, 2) if citations else 0.1

    audit_service.record(
        tenant_id, user_id, "copilot.chat", "interaction", "",
        f"intent={intent} citations={len(citations)} provider={usage.provider}",
    )

    return CopilotChatResponse(
        intent=intent,
        answer=answer,
        confidence_score=confidence,
        citations=citations,
        usage=usage,
    )
