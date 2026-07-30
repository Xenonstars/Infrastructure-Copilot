"""Application configuration.

In production, values come from environment variables / Azure Key Vault.
For the MVP everything has safe local defaults so it runs with ZERO setup.
"""
import os


class Settings:
    APP_NAME: str = "Infrastructure Copilot"
    VERSION: str = "0.1.0"

    # AI provider defaults. BYOK model: if no real provider is configured
    # per-tenant, the orchestrator falls back to the built-in MOCK provider,
    # so the whole system runs end-to-end without any API keys.
    DEFAULT_AI_PROVIDER: str = os.getenv("DEFAULT_AI_PROVIDER", "mock")

    # Retrieval tuning
    RAG_TOP_K: int = int(os.getenv("RAG_TOP_K", "5"))
    SIMILAR_INCIDENT_TOP_K: int = int(os.getenv("SIMILAR_INCIDENT_TOP_K", "5"))

    # Cost/limits (illustrative)
    MAX_PROMPT_TOKENS: int = int(os.getenv("MAX_PROMPT_TOKENS", "6000"))


settings = Settings()
