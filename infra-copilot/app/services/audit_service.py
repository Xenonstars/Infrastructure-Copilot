"""Audit service — every meaningful action gets a tenant-scoped record."""
from __future__ import annotations

from app.database import store
from app.domain import AuditEvent


def record(
    tenant_id: str,
    user_id: str,
    action: str,
    resource_type: str = "",
    resource_id: str = "",
    detail: str = "",
) -> AuditEvent:
    event = AuditEvent(
        tenant_id=tenant_id,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        detail=detail,
    )
    return store.add_audit(event)


def list_events(tenant_id: str):
    return store.list_audit(tenant_id)
