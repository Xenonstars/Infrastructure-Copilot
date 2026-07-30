"""Tenant admin endpoints (bootstrap; no tenant header required to create)."""
from __future__ import annotations

from fastapi import APIRouter

from app.domain import CreateTenantRequest, Tenant
from app.services import tenant_service

router = APIRouter(prefix="/api/v1/tenants", tags=["Tenants"])


@router.post("", response_model=Tenant, status_code=201)
def create_tenant(req: CreateTenantRequest) -> Tenant:
    return tenant_service.create_tenant(req)


@router.get("", response_model=list[Tenant])
def list_tenants() -> list[Tenant]:
    return tenant_service.list_tenants()


@router.get("/{tenant_id}", response_model=Tenant)
def get_tenant(tenant_id: str) -> Tenant:
    return tenant_service.get_tenant(tenant_id)
