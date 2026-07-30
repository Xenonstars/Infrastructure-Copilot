"""Domain models (Pydantic schemas) for Infrastructure Copilot MVP."""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _uuid() -> str:
    return str(uuid4())


# ---------- Tenants ----------
class PlanCode(str, Enum):
    starter = "starter"
    professional = "professional"
    msp = "msp"
    enterprise = "enterprise"


class Tenant(BaseModel):
    id: str = Field(default_factory=_uuid)
    tenant_code: str
    name: str
    plan_code: PlanCode = PlanCode.starter
    status: str = "active"
    created_at: datetime = Field(default_factory=_now)


class CreateTenantRequest(BaseModel):
    tenant_code: str
    name: str
    plan_code: PlanCode = PlanCode.starter


# ---------- AI Providers (BYOK) ----------
class AiProvider(BaseModel):
    id: str = Field(default_factory=_uuid)
    tenant_id: str
    display_name: str
    provider_type: str = "mock"          # mock | azure_openai | openai
    auth_mode: str = "none"              # none | api_key | entra_id
    endpoint_url: Optional[str] = None
    default_model: Optional[str] = None
    secret_reference: Optional[str] = None   # NEVER store the raw key
    status: str = "active"
    created_at: datetime = Field(default_factory=_now)


class CreateAiProviderRequest(BaseModel):
    display_name: str
    provider_type: str = "mock"
    auth_mode: str = "none"
    endpoint_url: Optional[str] = None
    default_model: Optional[str] = None
    # Raw secret only accepted over the wire; stored as a reference only.
    secret_value: Optional[str] = None


# ---------- Incidents ----------
class Incident(BaseModel):
    id: str = Field(default_factory=_uuid)
    tenant_id: str
    external_id: str
    source_system: str = "servicenow"
    title: str
    description: str = ""
    severity: str = "P3"
    status: str = "open"
    service_name: Optional[str] = None
    resolution: Optional[str] = None
    opened_at: datetime = Field(default_factory=_now)


class CreateIncidentRequest(BaseModel):
    external_id: str
    title: str
    description: str = ""
    severity: str = "P3"
    status: str = "open"
    service_name: Optional[str] = None
    resolution: Optional[str] = None
    source_system: str = "servicenow"


class SimilarIncident(BaseModel):
    incident: Incident
    similarity_score: float
    reason: str


# ---------- Knowledge ----------
class KnowledgeDocument(BaseModel):
    id: str = Field(default_factory=_uuid)
    tenant_id: str
    title: str
    source_type: str = "runbook"        # runbook | kb | sop | rca
    content: str
    created_at: datetime = Field(default_factory=_now)


class CreateKnowledgeRequest(BaseModel):
    title: str
    source_type: str = "runbook"
    content: str


class Citation(BaseModel):
    source_type: str
    source_id: str
    title: str
    excerpt: str = ""
    relevance_score: float = 0.0


# ---------- Copilot ----------
class CopilotChatRequest(BaseModel):
    message: str
    response_format: str = "chat"   # chat | rca | troubleshooting | executive_summary
    incident_id: Optional[str] = None


class AiUsage(BaseModel):
    provider: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class CopilotChatResponse(BaseModel):
    interaction_id: str = Field(default_factory=_uuid)
    intent: str
    answer: str
    confidence_score: float
    citations: list[Citation] = []
    usage: AiUsage


# ---------- Audit ----------
class AuditEvent(BaseModel):
    id: str = Field(default_factory=_uuid)
    tenant_id: str
    user_id: str
    action: str
    resource_type: str = ""
    resource_id: str = ""
    detail: str = ""
    created_at: datetime = Field(default_factory=_now)
