"""BYOK AI provider endpoints.

The raw secret is accepted over TLS but NEVER stored: we persist only a
secret_reference (a pointer to a vault entry). This mirrors the production
rule that keys live in Key Vault, not the app database.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.database import store
from app.domain import AiProvider, CreateAiProviderRequest
from app.security import TenantContext, get_tenant_context
from app.services import audit_service

router = APIRouter(prefix="/api/v1/ai-providers", tags=["AI Providers (BYOK)"])


@router.post("", response_model=AiProvider, status_code=201)
def create_provider(
    req: CreateAiProviderRequest,
    ctx: TenantContext = Depends(get_tenant_context),
) -> AiProvider:
    secret_reference = None
    if req.secret_value:
        # In production: write to Key Vault, keep only the reference.
        secret_reference = f"kv://infra-copilot/{ctx.tenant_id}/{req.display_name}"
    provider = AiProvider(
        tenant_id=ctx.tenant_id,
        display_name=req.display_name,
        provider_type=req.provider_type,
        auth_mode=req.auth_mode,
        endpoint_url=req.endpoint_url,
        default_model=req.default_model,
        secret_reference=secret_reference,
    )
    store.add_provider(provider)
    audit_service.record(
        ctx.tenant_id, ctx.user_id, "ai_provider.create", "ai_provider",
        provider.id, f"type={provider.provider_type}",
    )
    return provider


@router.get("", response_model=list[AiProvider])
def list_providers(ctx: TenantContext = Depends(get_tenant_context)) -> list[AiProvider]:
    # Note: secret_reference is returned, raw secret is never persisted.
    return store.list_providers(ctx.tenant_id)
