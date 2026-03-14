from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient

from app.main import app, settings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run sample triage inputs through the FastAPI app.")
    parser.add_argument(
        "--input",
        default="sample_inputs/messages.json",
        help="Path to the input JSON file.",
    )
    parser.add_argument(
        "--output",
        default="outputs/triage_results.json",
        help="Path to the output JSON file.",
    )
    parser.add_argument(
        "--mode",
        choices=("hosted", "mock"),
        default="mock",
        help="Use the hosted Gemini provider or the local mock provider.",
    )
    parser.add_argument(
        "--copy-to",
        default="",
        help="Optional second JSON file to write the same results to.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    project_root = PROJECT_ROOT
    input_path = project_root / args.input
    output_path = project_root / args.output
    copy_path = (project_root / args.copy_to) if args.copy_to else None

    messages = json.loads(input_path.read_text(encoding="utf-8"))

    settings.use_mock_llm = args.mode == "mock"
    settings.output_file = output_path

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("[]\n", encoding="utf-8")

    client = TestClient(app)
    results: list[dict[str, object]] = []
    for message in messages:
        response = client.post("/triage", json=message)
        response.raise_for_status()
        results.append(response.json())

    if copy_path:
        copy_path.parent.mkdir(parents=True, exist_ok=True)
        copy_path.write_text(json.dumps(results, indent=2), encoding="utf-8")

    print(f"Processed {len(results)} messages into {output_path}")


if __name__ == "__main__":
    main()
