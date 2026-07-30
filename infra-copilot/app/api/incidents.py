"""Incident endpoints — all tenant-scoped via TenantContext dependency."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.domain import CreateIncidentRequest, Incident, SimilarIncident
from app.security import TenantContext, get_tenant_context
from app.services import incident_service

router = APIRouter(prefix="/api/v1/incidents", tags=["Incidents"])


@router.post("", response_model=Incident, status_code=201)
def create_incident(
    req: CreateIncidentRequest,
    ctx: TenantContext = Depends(get_tenant_context),
) -> Incident:
    return incident_service.create_incident(ctx.tenant_id, ctx.user_id, req)


@router.get("", response_model=list[Incident])
def list_incidents(ctx: TenantContext = Depends(get_tenant_context)) -> list[Incident]:
    return incident_service.list_incidents(ctx.tenant_id)


@router.get("/{incident_id}", response_model=Incident)
def get_incident(
    incident_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
) -> Incident:
    return incident_service.get_incident(ctx.tenant_id, incident_id)


@router.post("/{incident_id}/similar", response_model=list[SimilarIncident])
def find_similar(
    incident_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
) -> list[SimilarIncident]:
    return incident_service.find_similar(ctx.tenant_id, incident_id, ctx.user_id)
