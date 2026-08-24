from __future__ import annotations

from app.core.config import get_settings
from app.providers.ai.base import AIProvider
from app.providers.ai.fallback import FallbackAIProvider
from app.providers.ai.openai_provider import OpenAIProvider


def get_ai_provider() -> AIProvider:
    s = get_settings()
    if not s.ai_enabled:
        return FallbackAIProvider()
    if s.ai_provider == "openai":
        return OpenAIProvider()
    return FallbackAIProvider()
