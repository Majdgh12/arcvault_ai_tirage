# Prompt Rationale

## Classification Prompt

The classification prompt is intentionally narrow. It constrains the model to five allowed categories, three allowed priority values, and a numeric confidence score so the downstream routing logic can remain deterministic and easy to audit. I also added a few decision rules for outages, billing disputes, and how-to questions so the model has explicit guidance around the most important edge cases. The main tradeoff is that this prompt favors consistency over nuance. With more time, I would add a few-shot examples for ambiguous tickets and compare how often the model confuses bug reports with incidents.

## Extraction Prompt

The extraction prompt focuses on fields that are immediately useful to the receiving team: core issue, identifiers, urgency, summary, and billing amount. The JSON-only instruction keeps the output easy to validate, while the field-level rules reduce drift in urgency labels and identifier formatting. The tradeoff is that the schema is deliberately compact, so it does not capture richer metadata like customer impact counts, affected product area, or suggested next action. With more time, I would add source-aware extraction hints, validate more identifier patterns, and expand the schema for downstream reporting.
