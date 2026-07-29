"""BYOK Model Gateway.

Resolves the tenant's AI provider and routes the request. If the tenant has
no real provider configured, it falls back to the built-in MOCK provider so
the entire system runs end-to-end WITHOUT any API keys.

Real providers (Azure OpenAI / OpenAI) plug in behind the same interface.
Keys are never stored here; production reads a secret_reference from a vault.
"""
from __future__ import annotations

from typing import Protocol

from app.database import store
from app.domain import AiUsage, Citation


def _approx_tokens(text: str) -> int:
    # ~4 chars per token heuristic; good enough for MVP cost accounting.
    return max(1, len(text) // 4)


class ModelProvider(Protocol):
    name: str
    model: str

    def generate(self, prompt: str, context: list[Citation]) -> str: ...


class MockProvider:
    """Deterministic, grounded provider. No network, no keys.

    It synthesises an answer strictly from retrieved context so the output is
    always traceable to citations — mirroring the 'no context, no answer' rule.
    """

    name = "mock"
    model = "mock-grounded-v1"

    def generate(self, prompt: str, context: list[Citation]) -> str:
        if not context:
            return (
                "I could not find any authorized grounding data for this query "
                "in your tenant. Please ingest relevant runbooks or incidents, "
                "then ask again."
            )
        lines = ["Based on your tenant's operational knowledge:\n"]
        for i, c in enumerate(context, 1):
            lines.append(f"{i}. [{c.source_type}:{c.source_id}] {c.title} — {c.excerpt}".rstrip())
        lines.append(
            "\nRecommended next step: validate the most relevant item above, "
            "check recent changes to the affected service, and follow the "
            "highest-scoring runbook."
        )
        return "\n".join(lines)


class AzureOpenAIProvider:
    """Placeholder for BYOK Azure OpenAI. Not called in the MVP demo.

    In production this uses the tenant's endpoint + a vault secret reference
    (or keyless Entra ID). Left unimplemented on purpose to keep the MVP
    runnable with zero credentials.
    """

    name = "azure_openai"

    def __init__(self, endpoint: str, model: str) -> None:
        self.endpoint = endpoint
        self.model = model or "gpt-4o"

    def generate(self, prompt: str, context: list[Citation]) -> str:  # pragma: no cover
        raise NotImplementedError(
            "Configure a real Azure OpenAI provider + secret reference to enable."
        )


def _resolve_provider(tenant_id: str) -> ModelProvider:
    p = store.active_provider(tenant_id)
    if p is None or p.provider_type == "mock":
        return MockProvider()
    if p.provider_type == "azure_openai":
        return AzureOpenAIProvider(p.endpoint_url or "", p.default_model or "gpt-4o")
    return MockProvider()


def complete(tenant_id: str, prompt: str, context: list[Citation]) -> tuple[str, AiUsage]:
    provider = _resolve_provider(tenant_id)
    answer = provider.generate(prompt, context)
    usage = AiUsage(
        provider=provider.name,
        model=provider.model,
        prompt_tokens=_approx_tokens(prompt),
        completion_tokens=_approx_tokens(answer),
        total_tokens=_approx_tokens(prompt) + _approx_tokens(answer),
    )
    return answer, usage
