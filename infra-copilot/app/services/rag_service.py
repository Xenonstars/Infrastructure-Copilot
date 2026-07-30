"""RAG retrieval service — tenant-scoped, authorization-first.

Retrieves grounding context from BOTH knowledge documents and incident
history. Every result carries the tenant boundary; nothing crosses tenants.
"""
from __future__ import annotations

from app.config import settings
from app.database import store
from app.domain import Citation
from app.services.similarity import cosine, vectorize


def retrieve(tenant_id: str, query: str, top_k: int | None = None) -> list[Citation]:
    top_k = top_k or settings.RAG_TOP_K
    qvec = vectorize(query)
    scored: list[Citation] = []

    # Knowledge documents
    for doc in store.list_documents(tenant_id):
        score = cosine(qvec, vectorize(f"{doc.title} {doc.content}"))
        if score > 0:
            scored.append(
                Citation(
                    source_type=doc.source_type,
                    source_id=doc.id,
                    title=doc.title,
                    excerpt=doc.content[:200],
                    relevance_score=score,
                )
            )

    # Incident history (past incidents are knowledge too)
    for inc in store.list_incidents(tenant_id):
        text = f"{inc.title} {inc.description} {inc.resolution or ''}"
        score = cosine(qvec, vectorize(text))
        if score > 0:
            excerpt = inc.resolution or inc.description or inc.title
            scored.append(
                Citation(
                    source_type="incident",
                    source_id=inc.external_id,
                    title=inc.title,
                    excerpt=excerpt[:200],
                    relevance_score=score,
                )
            )

    scored.sort(key=lambda c: c.relevance_score, reverse=True)
    return scored[:top_k]
