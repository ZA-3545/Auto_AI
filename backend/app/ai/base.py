"""AI provider abstraction (PLANNING.md Section B.4)."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from app.schemas.extraction import ExtractedRequirements

if TYPE_CHECKING:
    from app.schemas.comparison import BestForConclusion, FactorComparison
    from app.schemas.listing_analysis import (
        ExtractedListing,
        LabeledClaim,
        PriceAssessment,
    )
    from app.schemas.maintenance import ExtractedVehicleDescription
    from app.schemas.vehicle import VehicleRead


class AIProviderError(Exception):
    """Raised when the provider call fails or returns unusable output."""


class AIProvider(ABC):
    """
    Swap-friendly LLM boundary.

    Business logic must depend on this interface only — never on a concrete SDK.
    """

    name: str

    @abstractmethod
    def extract_requirements(self, message: str) -> ExtractedRequirements:
        """
        Extract structured car-buying requirements from a natural-language message.

        Must use structured output / function calling so the result validates
        against ExtractedRequirements. Must NOT invent cars or call search.
        """

    def extract_listing(self, listing_text: str) -> "ExtractedListing":
        """
        Extract structured listing fields from pasted text.

        Must NOT judge price or invent accident/mechanical certainty.
        Default raises so callers can inject a test double.
        """
        raise NotImplementedError("This provider does not support listing extraction.")

    def extract_vehicle_description(self, text: str) -> "ExtractedVehicleDescription":
        """
        Extract make/model/year/mileage from freeform vehicle description.

        Must NOT generate maintenance advice — structured fields only.
        """
        raise NotImplementedError(
            "This provider does not support vehicle description extraction."
        )

    def phrase_comparison(
        self,
        *,
        vehicles: list["VehicleRead"],
        factors: list["FactorComparison"],
        best_for: list["BestForConclusion"],
        best_overall: "BestForConclusion",
        requirements: ExtractedRequirements,
    ) -> str:
        """
        Turn an already-computed comparison into readable prose.

        Must NOT invent prices, specs, or winners — only rephrase the structured input.
        Default implementation raises so callers can fall back to a template.
        """
        raise NotImplementedError("This provider does not support comparison phrasing.")

    def phrase_listing_summary(
        self,
        *,
        extracted: "ExtractedListing",
        price_assessment: "PriceAssessment",
        red_flags: list["LabeledClaim"],
        missing_information: list["LabeledClaim"],
    ) -> str:
        """
        Phrase an already-computed listing analysis as short advisor prose.

        Must NOT invent facts or claim accident-free / perfect condition.
        """
        raise NotImplementedError(
            "This provider does not support listing summary phrasing."
        )

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """
        Return embedding vectors for each input text (RAG ingestion / query).

        Must not invent knowledge content — embeddings only.
        """
        raise NotImplementedError("This provider does not support embeddings.")

    def answer_from_knowledge(
        self,
        *,
        question: str,
        chunks: list[dict],
    ) -> str:
        """
        Answer a general knowledge question using ONLY the provided chunks.

        If chunks are empty, callers should skip this and return a don't-know
        template instead of inventing an answer.
        """
        raise NotImplementedError(
            "This provider does not support knowledge-grounded answers."
        )

    def answer_from_buying_advice(
        self,
        *,
        question: str,
        chunks: list[dict],
    ) -> str:
        """
        Answer a buying-decision question using ONLY the provided chunks.

        Must present trade-offs honestly — not push a purchase. Callers skip
        this when retrieval is empty.
        """
        raise NotImplementedError(
            "This provider does not support buying-advice-grounded answers."
        )

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Underlying model identifier for logging / response metadata."""
