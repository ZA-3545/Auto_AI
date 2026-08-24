"""Requirement extraction service — LLM orchestration only (Phase 3)."""

from __future__ import annotations

from typing import Optional

from app.ai.base import AIProvider, AIProviderError
from app.ai.factory import get_ai_provider
from app.core.llm_retry import with_llm_retry
from app.schemas.extraction import ExtractedRequirements, ExtractResponse


def extract_requirements(
    message: str,
    *,
    provider: Optional[AIProvider] = None,
) -> ExtractResponse:
    """
    Convert a natural-language message into validated ExtractedRequirements.

    Does not search the database, invent cars, or recommend vehicles.
    """
    text = message.strip()
    if not text:
        raise AIProviderError("Message must not be empty.")

    ai = provider or get_ai_provider()
    requirements = with_llm_retry(
        "extract_requirements",
        lambda: ai.extract_requirements(text),
    )

    # Defense in depth: re-validate so invalid LLM output is never silently accepted.
    validated = ExtractedRequirements.model_validate(requirements.model_dump())

    return ExtractResponse(
        requirements=validated,
        provider=ai.name,
        model=ai.model_name,
    )
