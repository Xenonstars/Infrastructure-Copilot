"""Audit endpoints — tenant-scoped compliance trail."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.domain import AuditEvent
from app.security import TenantContext, get_tenant_context
from app.services import audit_service

router = APIRouter(prefix="/api/v1/audit", tags=["Audit"])


@router.get("/events", response_model=list[AuditEvent])
def list_events(ctx: TenantContext = Depends(get_tenant_context)) -> list[AuditEvent]:
    return audit_service.list_events(ctx.tenant_id)
