from __future__ import annotations

import re

from app.models import ClassificationResult, ExtractionResult, TriageRequest


def classify_message_locally(payload: TriageRequest) -> ClassificationResult:
    text = _combined_text(payload)
    billing_amount = _extract_billing_amount(text)

    if _contains_any(text, ("outage", "down for all users", "system down", "breach", "security incident")):
        return ClassificationResult(category="Incident/Outage", priority="High", confidence=0.96)

    if _contains_any(
        text,
        (
            "several customers",
            "cannot log in",
            "500 error",
            "cannot access",
            "multiple users affected",
            "dashboard stopped loading",
            "stopped loading",
        ),
    ):
        return ClassificationResult(category="Incident/Outage", priority="High", confidence=0.91)

    if _looks_like_billing_issue(text):
        priority = "High" if billing_amount is not None and billing_amount > 500 else "Medium"
        confidence = 0.98 if "invoice #" in text or "charged" in text or "charge of" in text else 0.87
        return ClassificationResult(category="Billing Issue", priority=priority, confidence=confidence)

    if _contains_any(text, ("feature", "would be great", "support exporting", "google sheets", "enhancement", "integration", "idea")):
        return ClassificationResult(category="Feature Request", priority="Low", confidence=0.98)

    if _contains_any(text, ("how can", "how do", "api key", "general question", "is there a way", "?")):
        return ClassificationResult(category="Technical Question", priority="Low", confidence=0.95)

    if _contains_any(text, ("error", "bug", "issue", "broken", "fails", "failure", "slow", "takes", "load for one")):
        return ClassificationResult(category="Bug Report", priority="Medium", confidence=0.82)

    return ClassificationResult(category="Technical Question", priority="Medium", confidence=0.65)


def extract_message_details_locally(payload: TriageRequest) -> ExtractionResult:
    text = _combined_text(payload)
    category = classify_message_locally(payload).category
    identifiers = _extract_identifiers(text)
    billing_amount = _extract_billing_amount(text)
    urgency = _derive_urgency(text=text, category=category, billing_amount=billing_amount)
    core_issue = _build_core_issue(
        payload=payload,
        category=category,
        identifiers=identifiers,
        billing_amount=billing_amount,
    )
    summary = _build_summary(
        payload=payload,
        category=category,
        urgency=urgency,
        identifiers=identifiers,
        billing_amount=billing_amount,
    )

    return ExtractionResult(
        core_issue=core_issue,
        identifiers=identifiers,
        urgency=urgency,
        summary=summary,
        billing_amount=billing_amount,
    )


def _combined_text(payload: TriageRequest) -> str:
    parts = [payload.source or "", payload.subject or "", payload.message]
    return "\n".join(parts).lower()


def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    return any(keyword in text for keyword in keywords)


def _looks_like_billing_issue(text: str) -> bool:
    billing_keywords = (
        "invoice #",
        "charged",
        "charge of",
        "billing",
        "refund",
        "payment",
        "credit card",
        "contract rate",
        "reverse it",
    )
    return _contains_any(text, billing_keywords)


def _extract_identifiers(text: str) -> list[str]:
    patterns = (
        r"invoice\s*#\d+",
        r"account\s+id\s*[:#]?\s*[a-z0-9-]+",
        r"account\s*[:#]\s*[a-z0-9-]+",
        r"error code\s*[:#]?\s*[a-z0-9-]+",
        r"\barcvault\.io/[a-z0-9/_-]+\b",
        r"\b(?:err[-_ ]?\d+|[45]\d{2})\b",
    )

    found: list[str] = []
    seen: set[str] = set()
    for pattern in patterns:
        for match in re.findall(pattern, text, flags=re.IGNORECASE):
            value = match.strip()
            key = value.lower()
            if key not in seen:
                found.append(value)
                seen.add(key)

    return found


def _extract_billing_amount(text: str) -> float | None:
    match = re.search(r"\$([0-9][0-9,]*(?:\.[0-9]{1,2})?)", text)
    if not match:
        return None

    return float(match.group(1).replace(",", ""))


def _derive_urgency(*, text: str, category: str, billing_amount: float | None) -> str:
    if _contains_any(text, ("outage", "down for all users", "system down", "security", "breach", "multiple users affected")):
        return "critical"

    if category == "Incident/Outage":
        return "critical"

    if category == "Billing Issue" and billing_amount is not None and billing_amount > 500:
        return "high"

    if category == "Bug Report":
        return "medium"

    if category in {"Technical Question", "Feature Request"}:
        return "low"

    return "medium"


def _build_core_issue(
    *,
    payload: TriageRequest,
    category: str,
    identifiers: list[str],
    billing_amount: float | None,
) -> str:
    reference = _reference_text(payload)
    message = payload.message.strip().rstrip(".")

    if category == "Billing Issue" and identifiers and billing_amount is not None:
        return f"The customer reports a billing problem involving {identifiers[0]} and a stated amount of ${billing_amount:.0f}."

    if category == "Incident/Outage":
        return f"ArcVault appears to have a service-impacting access issue related to {reference.lower()}."

    if category == "Feature Request":
        return f"The customer is requesting a product enhancement related to {reference.lower()}."

    if category == "Technical Question":
        return f"The customer is asking for support guidance about {reference.lower()}."

    shortened_message = message[:120]
    if len(message) > 120:
        shortened_message += "..."
    return f"The customer reports the following issue: {shortened_message}"


def _build_summary(
    *,
    payload: TriageRequest,
    category: str,
    urgency: str,
    identifiers: list[str],
    billing_amount: float | None,
) -> str:
    if category == "Billing Issue":
        invoice_detail = identifiers[0] if identifiers else "the referenced invoice"
        amount_detail = f" for ${billing_amount:.0f}" if billing_amount is not None else ""
        return (
            f"This is a billing-related support request about {invoice_detail}{amount_detail}. "
            f"It should be reviewed by the billing team with {urgency} urgency."
        )

    if category == "Incident/Outage":
        if _contains_any(_combined_text(payload), ("security", "breach", "unfamiliar logins")):
            return (
                "The message indicates a potential security-related platform incident. "
                f"This should be treated as a {urgency} issue and reviewed quickly."
            )
        return (
            "The message indicates a broad access or availability problem affecting normal platform usage. "
            f"This should be treated as a {urgency} operational issue."
        )

    if category == "Feature Request":
        return (
            "This is a product improvement request rather than a defect or outage. "
            "It should be routed to the product queue for roadmap consideration."
        )

    if category == "Technical Question":
        return (
            "This is a how-to or support guidance request. "
            "It should be routed to the support queue for a standard response."
        )

    return (
        f"The ticket describes a product issue related to {_reference_text(payload)}. "
        f"It should be reviewed with {urgency} urgency."
    )


def _reference_text(payload: TriageRequest) -> str:
    if payload.subject:
        return payload.subject.strip().rstrip(".")

    message = payload.message.strip().rstrip(".")
    first_sentence = re.split(r"[.!?]", message, maxsplit=1)[0].strip()
    if first_sentence:
        return first_sentence[:80]

    return "the submitted request"
