# n8n Workflow Explanation

## Goal

Use n8n as the orchestration layer that receives inbound support traffic, calls the FastAPI triage service, and then stores or routes the structured result.

## Recommended Node Flow

1. **Webhook**
   - Method: `POST`
   - Path: `/arcvault/inbound`
   - Receives inbound JSON such as:
   ```json
   {
     "subject": "Billing question",
     "message": "We were charged twice for invoice #9922 for $720. Please investigate."
   }
   ```

2. **Set** (optional but useful)
   - Normalize the payload to the exact JSON expected by FastAPI:
   ```json
   {
     "subject": "={{$json.subject}}",
     "message": "={{$json.message}}"
   }
   ```

3. **HTTP Request**
   - Method: `POST`
   - URL: `http://localhost:8000/triage`
   - Send Body as JSON
   - Body:
   ```json
   {
     "subject": "={{$json.subject}}",
     "message": "={{$json.message}}"
   }
   ```
   - This node receives the structured triage result from FastAPI.

4. **IF**
   - Condition:
   ```text
   {{$json["escalation_flag"] === true}}
   ```
   - True branch means the ticket needs special handling.

5. **Storage Step**
   - True branch:
     - Append to an `Escalations` Google Sheet
     - Or write to a dedicated escalation file
   - False branch:
     - Append to a `Triage Results` Google Sheet
     - Or write to a standard results file

## What n8n Owns

n8n is responsible for:

- receiving inbound events
- triggering the API call
- branching on the API response
- forwarding or storing results

## What FastAPI Owns

FastAPI is responsible for:

- validation
- Gemini API calls
- classification
- extraction
- routing
- escalation logic
- JSON file persistence

## Why This Split Works

This division keeps the workflow clean. n8n remains a visual orchestrator, while FastAPI contains the logic that benefits from version-controlled Python code and typed models.

For a demo, this is enough:

- one webhook
- one API call
- one IF branch
- one storage action

That is simple to explain and professional enough for the assessment.
