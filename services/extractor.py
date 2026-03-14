from __future__ import annotations

from app.config import settings
from app.models import ExtractionResult, TriageRequest
from services.gemini_client import gemini_json_client
from services.mock_llm import extract_message_details_locally


EXTRACTION_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "core_issue": {"type": "string"},
        "identifiers": {
            "type": "array",
            "items": {"type": "string"},
        },
        "urgency": {
            "type": "string",
            "enum": ["low", "medium", "high", "critical"],
        },
        "summary": {"type": "string"},
        "billing_amount": {
            "type": ["number", "null"],
        },
    },
    "required": ["core_issue", "identifiers", "urgency", "summary", "billing_amount"],
    "additionalProperties": False,
}


def extract_message_details(payload: TriageRequest) -> ExtractionResult:
    if settings.use_mock_llm:
        return extract_message_details_locally(payload)

    try:
        result = gemini_json_client.run_prompt(
            settings.extraction_prompt_path,
            payload.model_dump(exclude_none=True),
            response_schema=EXTRACTION_RESPONSE_SCHEMA,
        )
        return ExtractionResult.model_validate(result)
    except Exception:
        if settings.llm_fallback_to_local:
            return extract_message_details_locally(payload)
        raise
