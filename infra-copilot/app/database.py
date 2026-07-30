"""In-memory, tenant-scoped data store for the MVP.

Every collection is keyed so that reads/writes MUST pass a tenant_id.
This mirrors the production rule: `tenant_id` on every row + RLS.
Swap this module for PostgreSQL repositories without touching services.
"""
from __future__ import annotations

from collections import defaultdict
from threading import RLock
from typing import Dict, List

from app.domain import (
    AiProvider,
    AuditEvent,
    Incident,
    KnowledgeDocument,
    Tenant,
)


class InMemoryStore:
    def __init__(self) -> None:
        self._lock = RLock()
        self.tenants: Dict[str, Tenant] = {}
        self.tenants_by_code: Dict[str, str] = {}
        # tenant_id -> list
        self.incidents: Dict[str, List[Incident]] = defaultdict(list)
        self.documents: Dict[str, List[KnowledgeDocument]] = defaultdict(list)
        self.providers: Dict[str, List[AiProvider]] = defaultdict(list)
        self.audit: Dict[str, List[AuditEvent]] = defaultdict(list)

    # ---- Tenants ----
    def add_tenant(self, tenant: Tenant) -> Tenant:
        with self._lock:
            self.tenants[tenant.id] = tenant
            self.tenants_by_code[tenant.tenant_code] = tenant.id
            return tenant

    def get_tenant(self, tenant_id: str) -> Tenant | None:
        return self.tenants.get(tenant_id)

    def list_tenants(self) -> List[Tenant]:
        return list(self.tenants.values())

    # ---- Incidents ----
    def add_incident(self, inc: Incident) -> Incident:
        with self._lock:
            self.incidents[inc.tenant_id].append(inc)
            return inc

    def list_incidents(self, tenant_id: str) -> List[Incident]:
        return list(self.incidents.get(tenant_id, []))

    def get_incident(self, tenant_id: str, incident_id: str) -> Incident | None:
        for inc in self.incidents.get(tenant_id, []):
            if inc.id == incident_id:
                return inc
        return None

    # ---- Knowledge ----
    def add_document(self, doc: KnowledgeDocument) -> KnowledgeDocument:
        with self._lock:
            self.documents[doc.tenant_id].append(doc)
            return doc

    def list_documents(self, tenant_id: str) -> List[KnowledgeDocument]:
        return list(self.documents.get(tenant_id, []))

    # ---- AI Providers ----
    def add_provider(self, p: AiProvider) -> AiProvider:
        with self._lock:
            self.providers[p.tenant_id].append(p)
            return p

    def list_providers(self, tenant_id: str) -> List[AiProvider]:
        return list(self.providers.get(tenant_id, []))

    def active_provider(self, tenant_id: str) -> AiProvider | None:
        for p in self.providers.get(tenant_id, []):
            if p.status == "active":
                return p
        return None

    # ---- Audit ----
    def add_audit(self, e: AuditEvent) -> AuditEvent:
        with self._lock:
            self.audit[e.tenant_id].append(e)
            return e

    def list_audit(self, tenant_id: str) -> List[AuditEvent]:
        return list(self.audit.get(tenant_id, []))


store = InMemoryStore()
