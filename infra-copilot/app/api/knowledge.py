"""Knowledge endpoints — ingest runbooks / KBs / SOPs / RCAs (tenant-scoped)."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.domain import CreateKnowledgeRequest, KnowledgeDocument
from app.security import TenantContext, get_tenant_context
from app.services import knowledge_service

router = APIRouter(prefix="/api/v1/knowledge", tags=["Knowledge"])


@router.post("/documents", response_model=KnowledgeDocument, status_code=201)
def create_document(
    req: CreateKnowledgeRequest,
    ctx: TenantContext = Depends(get_tenant_context),
) -> KnowledgeDocument:
    return knowledge_service.create_document(ctx.tenant_id, ctx.user_id, req)


@router.get("/documents", response_model=list[KnowledgeDocument])
def list_documents(ctx: TenantContext = Depends(get_tenant_context)) -> list[KnowledgeDocument]:
    return knowledge_service.list_documents(ctx.tenant_id)
