"""Incident service — CRUD + similar-incident search (tenant-scoped)."""
from __future__ import annotations

from fastapi import HTTPException

from app.config import settings
from app.database import store
from app.domain import (
    CreateIncidentRequest,
    Incident,
    SimilarIncident,
)
from app.services import audit_service
from app.services.similarity import cosine, vectorize


def _incident_text(inc: Incident) -> str:
    return f"{inc.title} {inc.description} {inc.service_name or ''} {inc.resolution or ''}"


def create_incident(tenant_id: str, user_id: str, req: CreateIncidentRequest) -> Incident:
    inc = Incident(tenant_id=tenant_id, **req.model_dump())
    store.add_incident(inc)
    audit_service.record(tenant_id, user_id, "incident.create", "incident", inc.id, inc.title)
    return inc


def list_incidents(tenant_id: str) -> list[Incident]:
    return store.list_incidents(tenant_id)


def get_incident(tenant_id: str, incident_id: str) -> Incident:
    inc = store.get_incident(tenant_id, incident_id)
    if inc is None:
        raise HTTPException(status_code=404, detail="Incident not found.")
    return inc


def find_similar(tenant_id: str, incident_id: str, user_id: str) -> list[SimilarIncident]:
    target = get_incident(tenant_id, incident_id)
    target_vec = vectorize(_incident_text(target))
    results: list[SimilarIncident] = []
    for inc in store.list_incidents(tenant_id):
        if inc.id == target.id:
            continue
        score = cosine(target_vec, vectorize(_incident_text(inc)))
        if score <= 0:
            continue
        reason = "Shared terms"
        if inc.service_name and inc.service_name == target.service_name:
            reason = f"Same service ({inc.service_name}) + shared terms"
        results.append(SimilarIncident(incident=inc, similarity_score=score, reason=reason))
    results.sort(key=lambda r: r.similarity_score, reverse=True)
    audit_service.record(
        tenant_id, user_id, "incident.find_similar", "incident", incident_id,
        f"{len(results)} candidates",
    )
    return results[: settings.SIMILAR_INCIDENT_TOP_K]
