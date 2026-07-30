"""Tenant context + (stubbed) identity.

Production: JWT from Entra ID/Okta -> validate -> resolve tenant + roles.
MVP: we read X-Tenant-Id and X-User-Id headers and enforce that the tenant
exists. This proves the isolation boundary: no request runs without a tenant.
"""
from __future__ import annotations

from dataclasses import dataclass

from fastapi import Header, HTTPException, status

from app.database import store


@dataclass
class TenantContext:
    tenant_id: str
    user_id: str
    roles: tuple[str, ...] = ("tenant.user",)


async def get_tenant_context(
    x_tenant_id: str = Header(..., alias="X-Tenant-Id"),
    x_user_id: str = Header("system", alias="X-User-Id"),
) -> TenantContext:
    tenant = store.get_tenant(x_tenant_id)
    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unknown or unauthorized tenant.",
        )
    return TenantContext(tenant_id=x_tenant_id, user_id=x_user_id)
