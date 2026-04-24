# titanic-agent

Enterprise automation flow that turns a raw product idea into a structured PRD, a Notion ticket, and a Stitch / Studio AI live UI preview. Built for Google Opal as the orchestration layer.

## Flow

1. **Raw Input** — Opal UI captures a plain-text product idea.
2. **Security Guardrail** — PII + RBAC scan. Blocks unauthorized data access and logs the attempt.
3. **PRD Generation** — PydanticAI agent (Gemini 3) emits a structured PRD JSON.
4. **Human-in-the-Loop** — TPM approval gate with audit log (required before Notion write).
5. **Notion Handshake** — Creates a page in the Innovation DB with Priority, TPM Lead, Status, Personas properties and a Project Overview body.
6. **Stitch / Studio AI** — Generates a preview link and posts it back to the Notion ticket (every link carries its `notion_page_id` for traceability).

## Repo layout

```
titanic_agent/
├── models.py          # Pydantic models + FlowState enum
├── security.py        # PII + RBAC guardrail
├── prd_agent.py       # PydanticAI / Gemini 3 agent
├── notion_client.py   # Notion API + tenacity retry + Slack fallback
├── stitch.py          # Stitch / Studio AI link builder
├── hitl.py            # Human-in-the-loop approval + audit log
├── orchestrator.py    # State machine: run_flow()
└── main.py            # Opal entrypoint, returns success JSON
tests/
├── fixtures.py        # RISKY_INPUT + SAFE_INPUT
├── test_security.py
├── test_orchestrator.py
└── test_notion_client.py
```

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .
cp .env.example .env   # fill in NOTION_TOKEN, NOTION_INNOVATION_DB_ID, GEMINI_API_KEY, SLACK_ALERT_WEBHOOK
pytest
python -m titanic_agent.main
```

## TPM checklist

- **Traceability** — every Studio AI link carries `notion_page_id`.
- **State management** — `tenacity` retries on Notion calls, Slack webhook fallback on failure.
- **Security** — all tokens via env vars (`os.environ`). Never hardcoded.
- **HITL** — approval logged before any external write.
