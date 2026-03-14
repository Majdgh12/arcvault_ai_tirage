from __future__ import annotations

from app.config import settings
from app.models import Category


ROUTE_MAP: dict[Category, str] = {
    "Bug Report": "Engineering",
    "Feature Request": "Product",
    "Billing Issue": "Billing",
    "Technical Question": "Support",
    "Incident/Outage": "IT/Security",
}


def determine_route(*, category: Category, confidence: float) -> str:
    if confidence < settings.confidence_threshold:
        return settings.fallback_queue

    return ROUTE_MAP.get(category, settings.fallback_queue)
