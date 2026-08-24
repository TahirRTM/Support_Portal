"""Typed application settings.

Production refuses to boot with weak/placeholder secrets. All secrets come from
the environment; nothing sensitive is hardcoded.
"""
from __future__ import annotations

import secrets
from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

WEAK_SECRETS = {"", "changeme", "secret", "password", "dev", "test", "placeholder"}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    # --- Runtime ---
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    app_name: str = "AI Support Portal"
    api_v1_prefix: str = "/api/v1"

    # --- Security / JWT ---
    access_token_secret: str = Field(default="dev-access-secret-not-for-prod-000000")
    refresh_token_secret: str = Field(default="dev-refresh-secret-not-for-prod-00000")
    jwt_algorithm: str = "HS256"
    access_token_ttl_seconds: int = 900          # 15 min
    refresh_token_ttl_seconds: int = 60 * 60 * 24 * 14  # 14 days
    client_session_ttl_seconds: int = 60 * 30     # 30 min scoped client session

    # --- Database ---
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/aisupport"

    # --- Redis ---
    redis_url: str = "redis://localhost:6379/0"

    # --- Trusted proxy / client IP ---
    trusted_proxies: list[str] = Field(default_factory=list)
    trust_forwarded_headers: bool = False

    # --- Rate limiting (client ticket creation) ---
    ticket_create_limit: int = 3
    ticket_create_window_seconds: int = 300

    # --- OTP ---
    otp_length: int = 6
    otp_ttl_seconds: int = 300
    otp_max_attempts: int = 5
    otp_resend_cooldown_seconds: int = 60

    # --- Cloudflare Turnstile ---
    turnstile_enabled: bool = True
    turnstile_secret_key: str = ""
    turnstile_verify_url: str = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
    turnstile_dev_bypass_token: str = "dev-bypass"

    # --- CORS ---
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    # --- Request limits ---
    max_request_body_bytes: int = 15 * 1024 * 1024  # 15 MB

    # --- Providers (all optional; abstractions degrade gracefully) ---
    ai_enabled: bool = True
    ai_provider: str = "openai"
    ai_api_key: str = ""
    ai_model: str = "gpt-4o-mini"
    ai_timeout_seconds: float = 20.0
    ai_max_output_tokens: int = 600

    email_provider: str = "smtp"
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    email_from: str = "support@example.com"

    whatsapp_provider: str = "meta"
    whatsapp_api_key: str = ""
    whatsapp_from: str = ""

    pushover_token: str = ""
    pushover_user_key: str = ""

    # --- Storage ---
    storage_backend: Literal["local", "s3"] = "local"
    storage_local_dir: str = "/var/lib/aisupport/attachments"
    s3_bucket: str = ""
    s3_endpoint_url: str = ""
    s3_region: str = "us-east-1"

    # --- ClamAV ---
    clamav_enabled: bool = True
    clamav_host: str = "clamav"
    clamav_port: int = 3310

    @field_validator("trusted_proxies", "cors_origins", mode="before")
    @classmethod
    def _split_csv(cls, v: object) -> object:
        if isinstance(v, str):
            return [x.strip() for x in v.split(",") if x.strip()]
        return v

    @model_validator(mode="after")
    def _enforce_prod_safety(self) -> "Settings":
        if self.environment == "production":
            problems: list[str] = []
            for name in ("access_token_secret", "refresh_token_secret"):
                val = getattr(self, name)
                if val.lower() in WEAK_SECRETS or len(val) < 32 or "not-for-prod" in val:
                    problems.append(name)
            if self.debug:
                problems.append("debug must be false in production")
            if self.access_token_secret == self.refresh_token_secret:
                problems.append("access and refresh secrets must differ")
            if self.turnstile_enabled and not self.turnstile_secret_key:
                problems.append("turnstile_secret_key required when turnstile enabled")
            if problems:
                raise ValueError(
                    "Unsafe production configuration: " + "; ".join(problems)
                )
        return self

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


def generate_secret() -> str:
    """Helper for operators to mint a strong secret."""
    return secrets.token_urlsafe(48)
