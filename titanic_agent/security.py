"""PII + RBAC security guardrail."""
from __future__ import annotations

import logging
import re

from .models import FlowContext, FlowState, SecurityResult

log = logging.getLogger("titanic_agent.security")

# Regex-based PII detection. Conservative, easy to extend.
PII_PATTERNS: dict[str, re.Pattern[str]] = {
    "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "credit_card": re.compile(r"\b(?:\d[ -]*?){13,19}\b"),
    "email": re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    "passport": re.compile(r"\bpassport\s*#?\s*[A-Z0-9]{6,9}\b", re.IGNORECASE),
    "dob": re.compile(r"\bdob[:\s]+\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", re.IGNORECASE),
    "salary": re.compile(r"\bsalary[:\s]+\$?\d{3,}", re.IGNORECASE),
}

# Minimum role required to touch a given resource keyword.
RBAC_RESTRICTED: dict[str, set[str]] = {
    "viewer": {"prod-db", "prod db", "finance", "pii", "payroll", "customer pii"},
    "pm": {"prod-db", "payroll"},
    "tpm": set(),  # full access in this demo
}


def security_check(ctx: FlowContext) -> FlowContext:
    """Run PII + RBAC checks. Mutates and returns ctx."""
    ctx.state = FlowState.SECURITY_CHECK
    if ctx.raw is None:
        ctx.security = SecurityResult(passed=False, sanitized_text="", reason="no raw input")
        ctx.state = FlowState.SECURITY_BLOCK
        return ctx

    text = ctx.raw.text
    lowered = text.lower()

    pii_hits = [name for name, rx in PII_PATTERNS.items() if rx.search(text)]
    role_restricted = RBAC_RESTRICTED.get(ctx.raw.role.lower(), set())
    rbac_hits = [kw for kw in role_restricted if kw in lowered]

    flagged = pii_hits + rbac_hits
    if flagged:
        ctx.security = SecurityResult(
            passed=False,
            sanitized_text="",
            flagged_terms=flagged,
            reason="PII detected" if pii_hits else "RBAC violation",
        )
        ctx.state = FlowState.SECURITY_BLOCK
        log.warning(
            "SECURITY_BLOCK user=%s role=%s flags=%s",
            ctx.raw.submitter, ctx.raw.role, flagged,
        )
        return ctx

    ctx.security = SecurityResult(passed=True, sanitized_text=text.strip())
    log.info("security_pass user=%s", ctx.raw.submitter)
    return ctx
