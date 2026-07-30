"""Knowledge service — ingest documents (runbooks, KBs, SOPs, RCAs)."""
from __future__ import annotations

from app.database import store
from app.domain import CreateKnowledgeRequest, KnowledgeDocument
from app.services import audit_service


def create_document(tenant_id: str, user_id: str, req: CreateKnowledgeRequest) -> KnowledgeDocument:
    doc = KnowledgeDocument(tenant_id=tenant_id, **req.model_dump())
    store.add_document(doc)
    audit_service.record(tenant_id, user_id, "knowledge.create", "document", doc.id, doc.title)
    return doc


def list_documents(tenant_id: str) -> list[KnowledgeDocument]:
    return store.list_documents(tenant_id)
