from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from google import genai

from app.config import settings


class GeminiJSONClient:
    def __init__(self) -> None:
        self._client: genai.Client | None = None

    def run_prompt(
        self,
        prompt_path: Path,
        payload: dict[str, Any],
        *,
        response_schema: dict[str, Any],
    ) -> dict[str, Any]:
        prompt_text = prompt_path.read_text(encoding="utf-8").strip()
        return self.generate_json(
            prompt_text=prompt_text,
            payload=payload,
            response_schema=response_schema,
        )

    def generate_json(
        self,
        *,
        prompt_text: str,
        payload: dict[str, Any],
        response_schema: dict[str, Any],
    ) -> dict[str, Any]:
        response = self._get_client().models.generate_content(
            model=settings.gemini_model,
            contents=self._build_input(prompt_text=prompt_text, payload=payload),
            config={
                "response_mime_type": "application/json",
                "response_json_schema": response_schema,
            },
        )
        raw_output = (response.text or "").strip()
        if not raw_output:
            raise ValueError("Gemini returned an empty response.")

        parsed = json.loads(raw_output)
        if not isinstance(parsed, dict):
            raise ValueError("Gemini response must be a JSON object.")

        return parsed

    def _get_client(self) -> genai.Client:
        if self._client is None:
            if not settings.gemini_api_key:
                raise RuntimeError("GEMINI_API_KEY is not set. Add it to your .env file.")
            self._client = genai.Client(api_key=settings.gemini_api_key)
        return self._client

    @staticmethod
    def _build_input(*, prompt_text: str, payload: dict[str, Any]) -> str:
        payload_json = json.dumps(payload, indent=2, ensure_ascii=True)
        return f"{prompt_text}\n\nInput JSON:\n{payload_json}"


gemini_json_client = GeminiJSONClient()
