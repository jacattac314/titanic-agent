"""Test fixtures for the security guardrail: safe vs risky inputs."""
from titanic_agent.models import RawIdea

SAFE_INPUT = RawIdea(
    submitter="jack.tpm@company.com",
    role="tpm",
    text=(
        "Build an automated auditor for our MLOps pipeline that flags "
        "high-latency models in St. Louis. Target P95 latency < 200ms."
    ),
)

# --- Risky inputs ---

RISKY_INPUT_PII = RawIdea(
    submitter="rogue@company.com",
    role="pm",
    text=(
        "Build a CRM dashboard that surfaces customer SSN 123-45-6789 and "
        "their saved credit card 4111 1111 1111 1111 next to salary: $180000."
    ),
)

RISKY_INPUT_RBAC = RawIdea(
    submitter="intern@company.com",
    role="viewer",
    text="Query the prod-db finance tables and export payroll to a spreadsheet.",
)

RISKY_INPUT_EMAIL = RawIdea(
    submitter="rogue@company.com",
    role="pm",
    text="Scrape contact emails like ceo@competitor.com and alert Slack.",
)
