from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.config import settings
from app.models import TriageResponse


def append_triage_result(result: TriageResponse) -> None:
    output_path = settings.output_file
    output_path.parent.mkdir(parents=True, exist_ok=True)

    records = _load_records(output_path)
    records.append(json.loads(result.model_dump_json()))
    output_path.write_text(json.dumps(records, indent=2), encoding="utf-8")


def _load_records(output_path: Path) -> list[dict[str, Any]]:
    if not output_path.exists():
        return []

    raw_content = output_path.read_text(encoding="utf-8").strip()
    if not raw_content:
        return []

    try:
        data = json.loads(raw_content)
    except json.JSONDecodeError:
        return []

    return data if isinstance(data, list) else []
