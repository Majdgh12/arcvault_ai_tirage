# Loom Demo Script

## 2-Minute Demo Script

Hi, this project is an AI-powered intake and triage pipeline for ArcVault, a fictional B2B software company.

The problem I'm solving is that inbound support messages arrive as unstructured text, but operations teams need them turned into structured data quickly so they can route and escalate consistently.

The architecture is intentionally simple. n8n acts as the orchestration layer, FastAPI is the AI decision layer, Gemini handles classification and enrichment, and results are appended to a local JSON file for persistence.

The flow starts when a support message hits an n8n webhook. n8n sends the subject and message to the FastAPI `/triage` endpoint. Inside FastAPI, there are two Gemini calls. The first classifies the ticket into one of five categories: Bug Report, Feature Request, Billing Issue, Technical Question, or Incident slash Outage. It also assigns a priority and a confidence score.

The second Gemini call enriches the message by extracting the core issue, identifiers like invoice numbers or error codes, an urgency signal, and a short summary.

After that, the backend applies deterministic Python logic. Routing maps the category to the correct queue, like Engineering, Product, Billing, Support, or IT slash Security. If the confidence score is below 0.7, it uses a fallback queue instead.

There is also escalation logic. A ticket is escalated if the confidence is low, if the message mentions terms like outage, system down, security, or breach, or if it is a billing issue over 500 dollars. Escalated tickets are sent to the Escalation Queue.

The final structured result is returned as JSON and appended to `outputs/triage_results.json`. That same response can be used by n8n to branch into an escalation path or store the result in Google Sheets.

This solution stays lightweight, readable, and production-minded without over-engineering the assessment.
