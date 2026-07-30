"""Copilot chat endpoint — the product's headline capability."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.domain import CopilotChatRequest, CopilotChatResponse
from app.security import TenantContext, get_tenant_context
from app.services import orchestrator

router = APIRouter(prefix="/api/v1/copilot", tags=["Copilot"])


@router.post("/chat", response_model=CopilotChatResponse)
def chat(
    req: CopilotChatRequest,
    ctx: TenantContext = Depends(get_tenant_context),
) -> CopilotChatResponse:
    return orchestrator.chat(ctx.tenant_id, ctx.user_id, req)
