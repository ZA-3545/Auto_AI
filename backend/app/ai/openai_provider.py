"""OpenAI-compatible provider — structured outputs via chat.completions.parse."""

from __future__ import annotations

from typing import Any, Optional

from openai import APIError, APIStatusError, OpenAI

from app.ai.base import AIProvider, AIProviderError
from app.ai.prompts import (
    EXTRACTION_SYSTEM_PROMPT,
    LISTING_EXTRACTION_SYSTEM_PROMPT,
    VEHICLE_DESCRIPTION_EXTRACTION_PROMPT,
)
from app.schemas.extraction import ExtractedRequirements
from app.schemas.listing_analysis import ExtractedListing
from app.schemas.maintenance import ExtractedVehicleDescription


def _friendly_api_error(exc: APIError, *, provider: str) -> str:
    status = getattr(exc, "status_code", None)
    code = None
    message = str(exc)
    body = getattr(exc, "body", None)
    if isinstance(body, dict):
        err = body.get("error") or {}
        if isinstance(err, dict):
            code = err.get("code")
            message = str(err.get("message") or message)

    if provider == "openrouter":
        if status in (402, 429) or code in {"insufficient_quota", "payment_required"}:
            return (
                "OpenRouter credit/quota error (HTTP "
                f"{status or 429}). Add credits at https://openrouter.ai/settings/credits "
                "or set OPENROUTER_API_KEY in backend/.env, then restart the API."
            )
        if status == 401 or code in {"invalid_api_key", "unauthorized"}:
            return (
                "OpenRouter rejected the API key (HTTP 401). Set a valid "
                "OPENROUTER_API_KEY (sk-or-v1-...) in backend/.env and restart the API."
            )
        if status in (408, 504) or "timeout" in message.lower():
            return "openrouter request timed out"
        return f"OpenRouter API error (HTTP {status or 'unknown'})"

    if status == 429 or code == "insufficient_quota":
        return (
            "OpenAI quota exceeded (HTTP 429). Add billing credit or use a different "
            "OPENAI_API_KEY in backend/.env, then restart the API. "
            "See https://platform.openai.com/account/billing"
        )
    if status == 401 or code == "invalid_api_key":
        return (
            "OpenAI rejected the API key (HTTP 401). Set a valid OPENAI_API_KEY in "
            "backend/.env and restart the API."
        )
    if status in (408, 504) or "timeout" in message.lower():
        return f"{provider} request timed out"
    return f"{provider} API error (HTTP {status or 'unknown'})"


class OpenAIProvider(AIProvider):
    name = "openai"

    def __init__(
        self,
        api_key: str,
        model: str,
        *,
        base_url: Optional[str] = None,
        extra_headers: Optional[dict[str, str]] = None,
        name: Optional[str] = None,
        missing_key_message: Optional[str] = None,
    ) -> None:
        if name:
            self.name = name
        if not api_key:
            raise AIProviderError(
                missing_key_message
                or "OPENAI_API_KEY is missing. Set it in backend/.env to use the OpenAI provider."
            )
        client_kwargs: dict[str, Any] = {"api_key": api_key}
        if base_url:
            client_kwargs["base_url"] = base_url
        if extra_headers:
            client_kwargs["default_headers"] = extra_headers
        from app.core.config import settings

        client_kwargs["timeout"] = settings.LLM_TIMEOUT_SECONDS
        self._client = OpenAI(**client_kwargs)
        self._model = model

    @property
    def model_name(self) -> str:
        return self._model

    def _log_usage(self, operation: str, completion: Any) -> None:
        usage = getattr(completion, "usage", None)
        if not usage:
            return
        from app.core.logging_config import log_llm_usage

        log_llm_usage(
            provider=self.name,
            model=self._model,
            operation=operation,
            prompt_tokens=getattr(usage, "prompt_tokens", None),
            completion_tokens=getattr(usage, "completion_tokens", None),
            total_tokens=getattr(usage, "total_tokens", None),
        )

    def extract_requirements(self, message: str) -> ExtractedRequirements:
        try:
            completion = self._client.chat.completions.parse(
                model=self._model,
                messages=[
                    {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                    {"role": "user", "content": message},
                ],
                response_format=ExtractedRequirements,
                temperature=0,
            )
            self._log_usage("extract_requirements", completion)
        except APIStatusError as exc:
            raise AIProviderError(
                _friendly_api_error(exc, provider=self.name)
            ) from exc
        except APIError as exc:
            raise AIProviderError(
                _friendly_api_error(exc, provider=self.name)
            ) from exc
        except Exception as exc:  # noqa: BLE001
            raise AIProviderError(
                f"{self.name} extraction failed: {exc}"
            ) from exc

        message_out = completion.choices[0].message
        if getattr(message_out, "refusal", None):
            raise AIProviderError(f"Model refused extraction: {message_out.refusal}")

        parsed = message_out.parsed
        if parsed is None:
            content = getattr(message_out, "content", None)
            if isinstance(content, str) and content.strip():
                try:
                    parsed = ExtractedRequirements.model_validate_json(content)
                except Exception as exc:
                    raise AIProviderError(
                        "Provider returned JSON that failed schema validation: "
                        f"{exc}"
                    ) from exc
            else:
                raise AIProviderError(
                    "Provider returned no parsed structured output (schema validation failed)."
                )

        try:
            return ExtractedRequirements.model_validate(parsed.model_dump())
        except Exception as exc:
            raise AIProviderError(
                f"Extracted requirements failed schema validation: {exc}"
            ) from exc

    def extract_listing(self, listing_text: str) -> ExtractedListing:
        try:
            completion = self._client.chat.completions.parse(
                model=self._model,
                messages=[
                    {"role": "system", "content": LISTING_EXTRACTION_SYSTEM_PROMPT},
                    {"role": "user", "content": listing_text},
                ],
                response_format=ExtractedListing,
                temperature=0,
            )
            self._log_usage("extract_listing", completion)
        except APIStatusError as exc:
            raise AIProviderError(
                _friendly_api_error(exc, provider=self.name)
            ) from exc
        except APIError as exc:
            raise AIProviderError(
                _friendly_api_error(exc, provider=self.name)
            ) from exc
        except Exception as exc:  # noqa: BLE001
            raise AIProviderError(
                f"{self.name} listing extraction failed: {exc}"
            ) from exc

        message_out = completion.choices[0].message
        if getattr(message_out, "refusal", None):
            raise AIProviderError(
                f"Model refused listing extraction: {message_out.refusal}"
            )

        parsed = message_out.parsed
        if parsed is None:
            content = getattr(message_out, "content", None)
            if isinstance(content, str) and content.strip():
                try:
                    parsed = ExtractedListing.model_validate_json(content)
                except Exception as exc:
                    raise AIProviderError(
                        "Provider returned listing JSON that failed schema "
                        f"validation: {exc}"
                    ) from exc
            else:
                raise AIProviderError(
                    "Provider returned no parsed listing structured output."
                )

        try:
            return ExtractedListing.model_validate(parsed.model_dump())
        except Exception as exc:
            raise AIProviderError(
                f"Extracted listing failed schema validation: {exc}"
            ) from exc

    def extract_vehicle_description(self, text: str) -> ExtractedVehicleDescription:
        try:
            completion = self._client.chat.completions.parse(
                model=self._model,
                messages=[
                    {
                        "role": "system",
                        "content": VEHICLE_DESCRIPTION_EXTRACTION_PROMPT,
                    },
                    {"role": "user", "content": text},
                ],
                response_format=ExtractedVehicleDescription,
                temperature=0,
            )
            self._log_usage("extract_vehicle_description", completion)
        except APIStatusError as exc:
            raise AIProviderError(
                _friendly_api_error(exc, provider=self.name)
            ) from exc
        except APIError as exc:
            raise AIProviderError(
                _friendly_api_error(exc, provider=self.name)
            ) from exc
        except Exception as exc:  # noqa: BLE001
            raise AIProviderError(
                f"{self.name} vehicle description extraction failed: {exc}"
            ) from exc

        message_out = completion.choices[0].message
        if getattr(message_out, "refusal", None):
            raise AIProviderError(
                f"Model refused vehicle description extraction: {message_out.refusal}"
            )

        parsed = message_out.parsed
        if parsed is None:
            content = getattr(message_out, "content", None)
            if isinstance(content, str) and content.strip():
                try:
                    parsed = ExtractedVehicleDescription.model_validate_json(content)
                except Exception as exc:
                    raise AIProviderError(
                        "Provider returned vehicle JSON that failed schema "
                        f"validation: {exc}"
                    ) from exc
            else:
                raise AIProviderError(
                    "Provider returned no parsed vehicle description output."
                )

        try:
            return ExtractedVehicleDescription.model_validate(parsed.model_dump())
        except Exception as exc:
            raise AIProviderError(
                f"Extracted vehicle description failed schema validation: {exc}"
            ) from exc

    def phrase_comparison(
        self,
        *,
        vehicles: list,
        factors: list,
        best_for: list,
        best_overall,
        requirements: ExtractedRequirements,
    ) -> str:
        from app.ai.prompts import COMPARISON_NARRATIVE_PROMPT

        payload = {
            "vehicles": [
                v.model_dump() if hasattr(v, "model_dump") else v for v in vehicles
            ],
            "factors": [
                f.model_dump() if hasattr(f, "model_dump") else f for f in factors
            ],
            "best_for": [
                b.model_dump() if hasattr(b, "model_dump") else b for b in best_for
            ],
            "best_overall": (
                best_overall.model_dump()
                if hasattr(best_overall, "model_dump")
                else best_overall
            ),
            "requirements": requirements.model_dump(),
        }

        try:
            completion = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": COMPARISON_NARRATIVE_PROMPT},
                    {
                        "role": "user",
                        "content": (
                            "Phrase this structured comparison as natural language. "
                            "Do not invent any data.\n\n"
                            f"{payload}"
                        ),
                    },
                ],
                temperature=0.3,
            )
            self._log_usage("phrase_comparison", completion)
        except APIStatusError as exc:
            raise AIProviderError(
                _friendly_api_error(exc, provider=self.name)
            ) from exc
        except APIError as exc:
            raise AIProviderError(
                _friendly_api_error(exc, provider=self.name)
            ) from exc
        except Exception as exc:  # noqa: BLE001
            raise AIProviderError(
                f"{self.name} comparison phrasing failed: {exc}"
            ) from exc

        content = completion.choices[0].message.content
        if not content or not str(content).strip():
            raise AIProviderError("Provider returned empty comparison narrative.")
        return str(content).strip()

    def phrase_listing_summary(
        self,
        *,
        extracted,
        price_assessment,
        red_flags: list,
        missing_information: list,
    ) -> str:
        from app.ai.prompts import LISTING_ADVISOR_SUMMARY_PROMPT

        payload = {
            "extracted": (
                extracted.model_dump()
                if hasattr(extracted, "model_dump")
                else extracted
            ),
            "price_assessment": (
                price_assessment.model_dump()
                if hasattr(price_assessment, "model_dump")
                else price_assessment
            ),
            "red_flags": [
                f.model_dump() if hasattr(f, "model_dump") else f for f in red_flags
            ],
            "missing_information": [
                m.model_dump() if hasattr(m, "model_dump") else m
                for m in missing_information
            ],
        }

        try:
            completion = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": LISTING_ADVISOR_SUMMARY_PROMPT},
                    {
                        "role": "user",
                        "content": (
                            "Phrase this structured listing analysis. "
                            "Do not invent any data or claim accident-free/"
                            "perfect condition.\n\n"
                            f"{payload}"
                        ),
                    },
                ],
                temperature=0.3,
            )
            self._log_usage("phrase_listing_summary", completion)
        except APIStatusError as exc:
            raise AIProviderError(
                _friendly_api_error(exc, provider=self.name)
            ) from exc
        except APIError as exc:
            raise AIProviderError(
                _friendly_api_error(exc, provider=self.name)
            ) from exc
        except Exception as exc:  # noqa: BLE001
            raise AIProviderError(
                f"{self.name} listing summary phrasing failed: {exc}"
            ) from exc

        content = completion.choices[0].message.content
        if not content or not str(content).strip():
            raise AIProviderError("Provider returned empty listing summary.")
        return str(content).strip()

    def _embedding_model(self) -> str:
        from app.core.config import settings

        return settings.embedding_model_resolved

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        cleaned = [t.strip() for t in texts if t and t.strip()]
        if not cleaned:
            return []
        try:
            response = self._client.embeddings.create(
                model=self._embedding_model(),
                input=cleaned,
            )
            self._log_usage("embed_texts", response)
        except APIStatusError as exc:
            raise AIProviderError(
                _friendly_api_error(exc, provider=self.name)
            ) from exc
        except APIError as exc:
            raise AIProviderError(
                _friendly_api_error(exc, provider=self.name)
            ) from exc
        except Exception as exc:  # noqa: BLE001
            raise AIProviderError(f"{self.name} embedding failed: {exc}") from exc

        by_index = {item.index: item.embedding for item in response.data}
        return [list(by_index[i]) for i in range(len(cleaned))]

    def answer_from_knowledge(self, *, question: str, chunks: list[dict]) -> str:
        from app.ai.prompts import KNOWLEDGE_RAG_SYSTEM_PROMPT

        if not chunks:
            raise AIProviderError(
                "Refusing to answer without retrieved knowledge chunks."
            )

        payload = {
            "question": question,
            "chunks": chunks,
            "instruction": (
                "Answer using only these chunks. If they are insufficient, say so."
            ),
        }
        try:
            completion = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": KNOWLEDGE_RAG_SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": (
                            "Answer this question using ONLY the retrieved chunks.\n\n"
                            f"{payload}"
                        ),
                    },
                ],
                temperature=0.2,
            )
            self._log_usage("answer_from_knowledge", completion)
        except APIStatusError as exc:
            raise AIProviderError(
                _friendly_api_error(exc, provider=self.name)
            ) from exc
        except APIError as exc:
            raise AIProviderError(
                _friendly_api_error(exc, provider=self.name)
            ) from exc
        except Exception as exc:  # noqa: BLE001
            raise AIProviderError(
                f"{self.name} knowledge answer failed: {exc}"
            ) from exc

        content = completion.choices[0].message.content
        if not content or not str(content).strip():
            raise AIProviderError("Provider returned empty knowledge answer.")
        return str(content).strip()

    def answer_from_buying_advice(self, *, question: str, chunks: list[dict]) -> str:
        from app.ai.prompts import BUYING_ADVICE_RAG_SYSTEM_PROMPT

        if not chunks:
            raise AIProviderError(
                "Refusing to answer without retrieved buying-advice chunks."
            )

        payload = {
            "question": question,
            "chunks": chunks,
            "instruction": (
                "Answer using only these chunks. Present trade-offs honestly. "
                "If they are insufficient, say so."
            ),
        }
        try:
            completion = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": BUYING_ADVICE_RAG_SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": (
                            "Answer this buying-advice question using ONLY the "
                            f"retrieved chunks.\n\n{payload}"
                        ),
                    },
                ],
                temperature=0.2,
            )
            self._log_usage("answer_from_buying_advice", completion)
        except APIStatusError as exc:
            raise AIProviderError(
                _friendly_api_error(exc, provider=self.name)
            ) from exc
        except APIError as exc:
            raise AIProviderError(
                _friendly_api_error(exc, provider=self.name)
            ) from exc
        except Exception as exc:  # noqa: BLE001
            raise AIProviderError(
                f"{self.name} buying advice answer failed: {exc}"
            ) from exc

        content = completion.choices[0].message.content
        if not content or not str(content).strip():
            raise AIProviderError("Provider returned empty buying advice answer.")
        return str(content).strip()
