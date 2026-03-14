from __future__ import annotations

import re

from app.config import settings
from app.models import ClassificationResult, ExtractionResult, TriageRequest


ESCALATION_KEYWORDS = (
    "outage",
    "system down",
    "down for all users",
    "multiple users affected",
    "security",
    "breach",
)


def should_escalate(
    *,
    payload: TriageRequest,
    classification: ClassificationResult,
    extraction: ExtractionResult,
) -> bool:
    if classification.confidence < settings.confidence_threshold:
        return True

    combined_text = f"{payload.source or ''}\n{payload.subject or ''}\n{payload.message}".lower()
    if any(keyword in combined_text for keyword in ESCALATION_KEYWORDS):
        return True

    billing_amount = extraction.billing_amount
    if billing_amount is None:
        billing_amount = _extract_billing_amount(combined_text)

    return classification.category == "Billing Issue" and billing_amount is not None and billing_amount > 500


def _extract_billing_amount(text: str) -> float | None:
    match = re.search(r"\$([0-9][0-9,]*(?:\.[0-9]{1,2})?)", text)
    if not match:
        return None

    return float(match.group(1).replace(",", ""))
