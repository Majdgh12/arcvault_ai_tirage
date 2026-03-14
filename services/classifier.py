from __future__ import annotations

from app.config import settings
from app.models import ClassificationResult, TriageRequest
from services.gemini_client import gemini_json_client
from services.mock_llm import classify_message_locally


CLASSIFICATION_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "category": {
            "type": "string",
            "enum": [
                "Bug Report",
                "Feature Request",
                "Billing Issue",
                "Technical Question",
                "Incident/Outage",
            ],
        },
        "priority": {
            "type": "string",
            "enum": ["Low", "Medium", "High"],
        },
        "confidence": {
            "type": "number",
            "minimum": 0,
            "maximum": 1,
        },
    },
    "required": ["category", "priority", "confidence"],
    "additionalProperties": False,
}


def classify_message(payload: TriageRequest) -> ClassificationResult:
    if settings.use_mock_llm:
        return classify_message_locally(payload)

    try:
        result = gemini_json_client.run_prompt(
            settings.classification_prompt_path,
            payload.model_dump(exclude_none=True),
            response_schema=CLASSIFICATION_RESPONSE_SCHEMA,
        )
        return ClassificationResult.model_validate(result)
    except Exception:
        if settings.llm_fallback_to_local:
            return classify_message_locally(payload)
        raise
