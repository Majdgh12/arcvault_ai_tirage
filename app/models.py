from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


Category = Literal[
    "Bug Report",
    "Feature Request",
    "Billing Issue",
    "Technical Question",
    "Incident/Outage",
]
Priority = Literal["Low", "Medium", "High"]
Urgency = Literal["low", "medium", "high", "critical"]


class TriageRequest(BaseModel):
    source: str | None = Field(default=None, max_length=100)
    subject: str | None = Field(default=None, max_length=200)
    message: str = Field(..., min_length=1)

    @field_validator("source", "subject", mode="before")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None

        cleaned = value.strip()
        return cleaned or None

    @field_validator("message")
    @classmethod
    def normalize_message(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("message must not be empty")
        return cleaned


class ClassificationResult(BaseModel):
    category: Category
    priority: Priority
    confidence: float = Field(..., ge=0, le=1)


class ExtractionResult(BaseModel):
    core_issue: str = Field(..., min_length=1)
    identifiers: list[str] = Field(default_factory=list)
    urgency: Urgency
    summary: str = Field(..., min_length=1)
    billing_amount: float | None = Field(default=None, ge=0)


class TriageResponse(BaseModel):
    source: str | None = None
    subject: str | None = None
    category: Category
    priority: Priority
    confidence: float = Field(..., ge=0, le=1)
    core_issue: str
    identifiers: list[str] = Field(default_factory=list)
    urgency: Urgency
    route_to: str
    escalation_flag: bool
    summary: str
    processed_at: datetime
