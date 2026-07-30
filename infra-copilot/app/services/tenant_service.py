"""Tenant provisioning service."""
from __future__ import annotations

from fastapi import HTTPException, status

from app.database import store
from app.domain import CreateTenantRequest, Tenant


def create_tenant(req: CreateTenantRequest) -> Tenant:
    if req.tenant_code in store.tenants_by_code:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Tenant code '{req.tenant_code}' already exists.",
        )
    tenant = Tenant(tenant_code=req.tenant_code, name=req.name, plan_code=req.plan_code)
    return store.add_tenant(tenant)


def get_tenant(tenant_id: str) -> Tenant:
    tenant = store.get_tenant(tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail="Tenant not found.")
    return tenant


def list_tenants():
    return store.list_tenants()
