# ArcVault AI Triage Architecture

## Overview

This solution implements a lightweight AI-powered intake and triage pipeline for ArcVault, a fictional B2B software company. The design intentionally stays small and readable so it can be built and explained within a take-home assessment while still demonstrating sound backend architecture choices.

The system uses four simple building blocks:

1. `n8n` receives inbound support traffic through a webhook and orchestrates the workflow.
2. `FastAPI` exposes a `/triage` endpoint and acts as the decision layer.
3. `Gemini API` performs the two AI tasks: classification and structured extraction.
4. A local `JSON` file stores processed results for traceability and demo purposes.

This keeps the architecture understandable, cheap to run, and easy to extend later without introducing unnecessary infrastructure.

## Model Choice

The hosted model for this implementation is `gemini-2.5-flash`. It is a good fit for this scope because the workload is mostly short-form text classification and structured extraction, so speed and predictable JSON output matter more than deep reasoning depth. The repository also includes a local `mock` mode for offline testing and quota-free validation, but the intended hosted path is Gemini.

## Request Flow

The end-to-end request lifecycle is:

1. A support message is sent to an n8n webhook or directly to the FastAPI service during local testing.
2. The request forwards `message` plus optional `source` and `subject` fields to `POST /triage` in FastAPI.
3. FastAPI calls the Gemini API once for classification.
4. FastAPI calls the Gemini API again for extraction and enrichment.
5. Python business rules determine the route and escalation state.
6. FastAPI writes the structured result to `outputs/triage_results.json`.
7. FastAPI returns the same structured payload to n8n.
8. n8n can branch on `escalation_flag` and store the result in Google Sheets or another file target.

This is a hybrid design because the orchestration concerns stay in n8n and the decision logic stays in code. That separation keeps the workflow tool simple and keeps business logic testable and readable in Python.

## Why FastAPI for the Decision Layer

FastAPI is a good fit because the assessment only needs one clear API endpoint, typed request and response models, and straightforward local execution. It offers:

- Automatic input validation through Pydantic
- Clean JSON serialization
- Fast local development with Uvicorn
- A professional API surface without extra boilerplate

The backend is intentionally thin. It does not try to become a full support platform. Its job is to receive a message, turn it into structured triage data, and return the result.

## Why Two Gemini Calls

The system uses two separate prompts instead of one large prompt.

The first call handles classification:

- category
- priority
- confidence

The second call handles enrichment:

- core issue
- identifiers
- urgency
- short summary
- billing amount

Splitting these responsibilities keeps prompts simpler and makes failures easier to reason about. It also mirrors a common production pattern where a service first decides what something is, then enriches it with structured details.

Prompts require strict JSON output, and the backend validates the returned payloads with Pydantic models. This gives a practical balance between LLM flexibility and deterministic downstream handling.

## Routing Logic

Routing is implemented in Python rather than the LLM. That is deliberate.

Queue mapping is deterministic and belongs in application logic:

- Bug Report -> Engineering
- Feature Request -> Product
- Billing Issue -> Billing
- Technical Question -> Support
- Incident/Outage -> IT/Security

If model confidence is below `0.7`, the request is routed to the `Fallback Queue`. This prevents low-confidence model outputs from driving a high-trust downstream action.

Keeping routing in Python also makes the system easier to audit. If a business stakeholder wants to change a queue name or threshold, it is a small code change rather than a prompt rewrite.

## Escalation Logic

Escalation is also implemented in Python because it is a policy decision, not a language problem.

The service escalates when any of the following are true:

- confidence is below `0.7`
- the message contains `outage`, `system down`, `down for all users`, `security`, or `breach`
- the issue is a billing issue involving more than `$500`

When an item is escalated, the final route becomes `Escalation Queue`, regardless of the normal category mapping.

This pattern is useful because it allows AI to enrich the data while still letting deterministic rules handle operational risk. For example, a billing message might correctly classify as `Billing Issue`, but if the amount is large enough, operations may want it reviewed by a more senior queue immediately.

## Storage Strategy

For this assignment, JSON file storage is the right tradeoff.

Each processed record is appended to `outputs/triage_results.json`. That keeps the project easy to run locally without introducing a database. It also gives a clear artifact for a reviewer to inspect after running test messages.

This storage choice would not be ideal for a high-throughput production system, but it is perfectly appropriate for a take-home scope:

- easy to inspect
- zero setup cost
- works well for demos
- enough to prove structured output persistence

## Tradeoffs and Future Evolution

The project intentionally avoids vector databases, queues, workers, and containerization. Those tools can be useful, but they would add complexity without improving the core demonstration.

If this were expanded beyond the assessment, the next steps would likely be:

- add unit tests around routing and escalation
- move storage from JSON to a relational database
- add authentication and request logging
- add retry handling around Gemini API calls
- expose metrics for queue volume and escalation rates

The current architecture is therefore not a toy, but it is correctly scoped. It demonstrates orchestration, typed backend design, LLM integration, deterministic policy logic, and durable structured output in a package that can be built in a few hours and explained in a short demo.
