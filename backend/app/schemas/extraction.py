"""Extracted car-buying requirements (PLANNING.md Section D).

Validated against this schema at every LLM boundary — invalid output is rejected.
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, model_validator


class ConditionPreference(str, Enum):
    new = "new"
    used = "used"


class TransmissionPreference(str, Enum):
    automatic = "automatic"
    manual = "manual"


class ExtractedRequirements(BaseModel):
    """
    Structured requirement JSON returned by POST /api/chat/extract.

    Phase 3: extraction only — no vehicle lists, recommendations, or invented cars.
    """

    budget_min: Optional[int] = Field(
        default=None,
        description="Minimum budget in whole PKR, or null if not stated.",
    )
    budget_max: Optional[int] = Field(
        default=None,
        description=(
            "Maximum budget in whole PKR (e.g. 35 lakh → 3500000). "
            "Null if not stated or if the amount is ambiguous."
        ),
    )
    city: Optional[str] = Field(
        default=None,
        description="Preferred Pakistani city name, or null if not stated.",
    )
    condition: Optional[ConditionPreference] = Field(
        default=None,
        description="new or used, or null if not stated.",
    )
    transmission: Optional[TransmissionPreference] = Field(
        default=None,
        description="automatic or manual, or null if not stated.",
    )
    body_type: Optional[str] = Field(
        default=None,
        description=(
            "Body type if clearly stated (sedan, hatchback, suv, crossover, "
            "pickup, van, coupe), otherwise null."
        ),
    )
    purpose: Optional[str] = Field(
        default=None,
        description="Use purpose if stated (e.g. family, commute, business), else null.",
    )
    fuel_priority: Optional[bool] = Field(
        default=None,
        description="True if user prioritizes fuel economy; null if not mentioned.",
    )
    resale_priority: Optional[bool] = Field(
        default=None,
        description="True if user prioritizes resale value; null if not mentioned.",
    )
    needs_clarification: bool = Field(
        description=(
            "True when a critical value is ambiguous (especially a bare number "
            "budget without lakh/PKR/crore units). Do not guess in that case."
        ),
    )
    clarification_question: Optional[str] = Field(
        default=None,
        description=(
            "A short clarifying question when needs_clarification is true "
            "(e.g. 'Do you mean PKR 30 lakh?'). Null when no clarification needed."
        ),
    )

    @model_validator(mode="after")
    def clarification_consistency(self) -> "ExtractedRequirements":
        if self.needs_clarification and not (
            self.clarification_question and self.clarification_question.strip()
        ):
            raise ValueError(
                "clarification_question is required when needs_clarification is true"
            )
        if not self.needs_clarification:
            # Normalize empty strings to null when no clarification is needed
            object.__setattr__(self, "clarification_question", None)
        return self


class ExtractRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    conversation_id: Optional[str] = Field(
        default=None,
        description="Existing conversation UUID. Omit to start a new session.",
    )
    reset: bool = Field(
        default=False,
        description="If true, clear stored requirements before applying this turn.",
    )


class ExtractResponse(BaseModel):
    requirements: ExtractedRequirements
    provider: str
    model: str
    conversation_id: Optional[str] = None
    turn_requirements: Optional[ExtractedRequirements] = Field(
        default=None,
        description="Fields extracted from this turn only (before merge).",
    )
    reset: bool = False


class ResetRequest(BaseModel):
    conversation_id: str


class ResetResponse(BaseModel):
    conversation_id: str
    requirements: ExtractedRequirements
    message: str = "Requirements cleared. You can start a new search."


class ConversationCreateResponse(BaseModel):
    conversation_id: str
    requirements: ExtractedRequirements
