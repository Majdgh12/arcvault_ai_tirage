# ArcVault AI Triage

## Project Overview

ArcVault AI Triage is a small, runnable intake and triage system for customer support messages. It uses `FastAPI` for the decision layer, the `Gemini API` for classification and enrichment, and a local JSON file for structured output storage. The repository also contains an n8n workflow explanation, but the API can be tested directly without n8n.

The goal is to accept an inbound support message, classify it, enrich it with structured metadata, route it to the correct queue, decide whether it should be escalated, and persist the result.

## Architecture Explanation

Request flow:

`Inbound message -> FastAPI /triage -> Gemini classification -> Gemini extraction -> Python routing -> Python escalation -> JSON response -> outputs/triage_results.json`

Responsibilities:

- `FastAPI` validates input and coordinates the triage pipeline.
- `Gemini` produces structured classification and extraction outputs.
- `Python logic` owns routing and escalation policies.
- `JSON storage` provides simple persistence for the assessment.

Additional details are in `docs/architecture.md`, `docs/n8n_workflow.md`, and `docs/prompt_rationale.md`.

## Model Choice

This project is configured for `gemini-2.5-flash` because it is fast, supports structured JSON output, and fits the classification-plus-enrichment workflow well. The repository also keeps a `mock` mode for offline validation and quota-free local testing, but the intended hosted path is Gemini.

## File Tree

```text
arcvault_ai_triage/
|-- app/
|   |-- __init__.py
|   |-- config.py
|   |-- main.py
|   `-- models.py
|-- docs/
|   |-- architecture.md
|   |-- example_output.json
|   |-- loom_demo_script.md
|   |-- n8n_workflow.md
|   `-- prompt_rationale.md
|-- outputs/
|   `-- triage_results.json
|-- prompts/
|   |-- classification_prompt.txt
|   `-- extraction_prompt.txt
|-- scripts/
|   `-- run_sample_triage.py
|-- sample_inputs/
|   |-- extended_messages.json
|   `-- messages.json
|-- services/
|   |-- __init__.py
|   |-- classifier.py
|   |-- escalation.py
|   |-- extractor.py
|   |-- gemini_client.py
|   |-- router.py
|   `-- storage.py
|-- .env.example
|-- README.md
`-- requirements.txt
```

## Setup Instructions

1. Create and activate a Python 3.11 virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and set your Gemini API key:

```powershell
Copy-Item .env.example .env
```

4. Update `.env`:

```env
GEMINI_API_KEY=your_real_key
GEMINI_MODEL=gemini-2.5-flash
USE_MOCK_LLM=false
LLM_FALLBACK_TO_LOCAL=true
CONFIDENCE_THRESHOLD=0.7
OUTPUT_FILE=outputs/triage_results.json
FALLBACK_QUEUE=Fallback Queue
ESCALATION_QUEUE=Escalation Queue
```

If your Gemini account does not have access to `gemini-2.5-flash`, switch `GEMINI_MODEL` to another supported Gemini model available in your account.

If you do not want to use Gemini during local testing, set `USE_MOCK_LLM=true` to run the project in a local demo mode. You can also leave `USE_MOCK_LLM=false` and keep `LLM_FALLBACK_TO_LOCAL=true` so the app automatically falls back to local logic when the hosted model returns quota or connectivity errors.

## How To Run FastAPI

From the project root:

```bash
uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.

Useful endpoints:

- `GET /health`
- `POST /triage`

When local mode is enabled, `GET /health` will show `llm_mode: "mock"`. In hosted mode, the same endpoint will show `provider: "gemini"`.

`POST /triage` accepts:

- `message` required
- `source` optional
- `subject` optional

## Testing The Sample Sets

Use the built-in runner to generate clean outputs before moving into n8n.

Required five assessment messages:

```powershell
.\.venv\Scripts\python.exe scripts\run_sample_triage.py --input sample_inputs/messages.json --output outputs/triage_results.json --mode mock --copy-to docs/example_output.json
```

Extended mixed set with and without subjects:

```powershell
.\.venv\Scripts\python.exe scripts\run_sample_triage.py --input sample_inputs/extended_messages.json --output outputs/extended_triage_results.json --mode mock
```

If you want to use hosted Gemini instead of mock mode, change `--mode mock` to `--mode hosted` after setting a real `GEMINI_API_KEY` in `.env`.

## Example curl Request

```bash
curl -X POST http://localhost:8000/triage \
  -H "Content-Type: application/json" \
  -d '{
    "source": "Support Portal",
    "message": "Invoice #8821 shows a charge of $1,240 but our contract rate is $980/month. Can someone look into this?"
  }'
```

## Example Response

```json
{
  "source": "Support Portal",
  "subject": null,
  "category": "Billing Issue",
  "priority": "High",
  "confidence": 0.99,
  "core_issue": "The customer reports a billing problem involving invoice #8821 and a stated amount of $1240.",
  "identifiers": [
    "invoice #8821"
  ],
  "urgency": "high",
  "route_to": "Escalation Queue",
  "escalation_flag": true,
  "summary": "This is a billing-related support request about invoice #8821 for $1240. It should be reviewed by the billing team with high urgency.",
  "processed_at": "2026-03-13T08:32:00Z"
}
```

An expanded example output set is included in `docs/example_output.json`.

## How n8n Connects

Recommended workflow:

1. `Webhook` receives the inbound message.
2. `HTTP Request` sends `subject` and `message` to `POST /triage`.
3. `IF` checks whether `escalation_flag` is `true`.
4. `Google Sheets` or file storage writes the structured output to the appropriate destination.

The backend also appends every processed result to `outputs/triage_results.json`, so the n8n storage step is useful for orchestration and reporting, not for core persistence only.

See `docs/n8n_workflow.md` for the node-by-node explanation.

## Sample Test Input File

The exact required Valsoft sample messages are provided in:

- `sample_inputs/messages.json`

Additional mixed test cases with and without subjects are provided in:

- `sample_inputs/extended_messages.json`

## Future Improvements

- Add unit tests for routing, escalation, and storage.
- Add retry handling and timeout management around Gemini API calls.
- Add request logging and audit metadata.
- Replace JSON file storage with a database for production scale.
- Add authentication if the API is exposed beyond a local demo.

## Notes

- The prompts enforce JSON-only output and the backend validates results with Pydantic.
- Routing and escalation remain deterministic in Python instead of being delegated to the LLM.
- The implementation intentionally avoids Docker, queues, RAG, vector databases, and other extra infrastructure to keep the assessment scoped and readable.
