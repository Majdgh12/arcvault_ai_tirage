from __future__ import annotations

from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.models import TriageRequest, TriageResponse
from services.classifier import classify_message
from services.escalation import should_escalate
from services.extractor import extract_message_details
from services.router import determine_route
from services.storage import append_triage_result


app = FastAPI(
    title="ArcVault AI Triage API",
    version="1.0.0",
    description="AI-powered intake and triage pipeline for ArcVault support messages.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root() -> dict[str, str]:
    return {"service": "arcvault-ai-triage", "status": "running"}


@app.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "provider": settings.llm_provider,
        "model": settings.gemini_model,
        "llm_mode": "mock" if settings.use_mock_llm else "hosted",
        "fallback_mode": "enabled" if settings.llm_fallback_to_local else "disabled",
        "cors_origins": ",".join(settings.cors_origins),
        "output_file": str(settings.output_file),
    }


@app.post("/triage", response_model=TriageResponse)
def triage_message(payload: TriageRequest) -> TriageResponse:
    try:
        classification = classify_message(payload)
        extraction = extract_message_details(payload)
        default_route = determine_route(
            category=classification.category,
            confidence=classification.confidence,
        )
        escalation_flag = should_escalate(
            payload=payload,
            classification=classification,
            extraction=extraction,
        )
        route_to = settings.escalation_queue if escalation_flag else default_route

        result = TriageResponse(
            source=payload.source,
            subject=payload.subject,
            category=classification.category,
            priority=classification.priority,
            confidence=classification.confidence,
            core_issue=extraction.core_issue,
            identifiers=extraction.identifiers,
            urgency=extraction.urgency,
            route_to=route_to,
            escalation_flag=escalation_flag,
            summary=extraction.summary,
            processed_at=datetime.now(timezone.utc),
        )

        append_triage_result(result)
        return result
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Triage processing failed: {exc}",
        ) from exc
