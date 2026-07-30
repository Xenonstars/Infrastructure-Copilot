"""Infrastructure Copilot MVP — FastAPI application entrypoint.

Run:
    uvicorn app.main:app --reload
Docs (auto OpenAPI):
    http://localhost:8000/docs
"""
from __future__ import annotations

from fastapi import FastAPI

from app.api import ai_providers, audit, copilot, incidents, knowledge, tenants
from app.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description=(
        "AI-powered Incident & Change Intelligence Platform (MVP). "
        "Multi-tenant, BYOK, RAG-grounded, audited. Runs with zero API keys "
        "using the built-in mock model provider."
    ),
)

app.include_router(tenants.router)
app.include_router(ai_providers.router)
app.include_router(incidents.router)
app.include_router(knowledge.router)
app.include_router(copilot.router)
app.include_router(audit.router)


@app.get("/health", tags=["System"])
def health() -> dict:
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.VERSION}


@app.get("/", tags=["System"])
def root() -> dict:
    return {
        "message": "Infrastructure Copilot MVP is running.",
        "docs": "/docs",
        "default_ai_provider": settings.DEFAULT_AI_PROVIDER,
    }
