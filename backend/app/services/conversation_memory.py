"""
Conversation requirement merge + reset helpers (PLANNING.md Section G).

Pure deterministic logic — no LLM.
"""

from __future__ import annotations

import re

from app.schemas.extraction import ExtractedRequirements

# Phrases that clear stored requirements and start fresh
RESET_PHRASE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\bstart\s+(a\s+)?new\s+search\b", re.I),
    re.compile(r"\bnew\s+search\b", re.I),
    re.compile(r"\bstart\s+over\b", re.I),
    re.compile(r"\breset\s+(the\s+)?(search|filters|requirements)?\b", re.I),
    re.compile(r"\bclear\s+(my\s+)?(search|filters|requirements)\b", re.I),
]

# Fields merged across turns (exclude clarification metadata)
MERGEABLE_FIELDS = (
    "budget_min",
    "budget_max",
    "city",
    "condition",
    "transmission",
    "body_type",
    "purpose",
    "fuel_priority",
    "resale_priority",
)


def empty_requirements() -> ExtractedRequirements:
    return ExtractedRequirements(
        needs_clarification=False,
        clarification_question=None,
    )


def is_reset_message(message: str) -> bool:
    text = message.strip()
    if not text:
        return False
    return any(p.search(text) for p in RESET_PHRASE_PATTERNS)


def requirements_from_storage(data: dict | None) -> ExtractedRequirements:
    if not data:
        return empty_requirements()
    try:
        return ExtractedRequirements.model_validate(data)
    except Exception:
        return empty_requirements()


def merge_requirements(
    previous: ExtractedRequirements,
    new: ExtractedRequirements,
) -> ExtractedRequirements:
    """
    Merge newly extracted fields onto previous session requirements.

    Non-null values from `new` overwrite/add. Nulls leave previous values intact.
    Clarification is kept only when the ambiguous field is still missing after merge.
    """
    merged = previous.model_dump()
    incoming = new.model_dump()

    for field in MERGEABLE_FIELDS:
        value = incoming.get(field)
        if value is not None:
            merged[field] = value

    if new.needs_clarification:
        # Budget ambiguity is the main case — keep asking only if still unresolved
        budget_still_missing = (
            merged.get("budget_max") is None and merged.get("budget_min") is None
        )
        if budget_still_missing and new.clarification_question:
            merged["needs_clarification"] = True
            merged["clarification_question"] = new.clarification_question
        else:
            merged["needs_clarification"] = False
            merged["clarification_question"] = None
    else:
        merged["needs_clarification"] = False
        merged["clarification_question"] = None

    return ExtractedRequirements.model_validate(merged)
