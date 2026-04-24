"""Security guardrail tests: safe vs risky inputs."""
from titanic_agent.models import FlowContext, FlowState
from titanic_agent.security import security_check

from .fixtures import RISKY_INPUT_EMAIL, RISKY_INPUT_PII, RISKY_INPUT_RBAC, SAFE_INPUT


def test_safe_input_passes():
    ctx = security_check(FlowContext(raw=SAFE_INPUT))
    assert ctx.security is not None
    assert ctx.security.passed is True
    assert ctx.state == FlowState.SECURITY_CHECK
    assert ctx.security.sanitized_text.startswith("Build an automated auditor")


def test_pii_input_blocks():
    ctx = security_check(FlowContext(raw=RISKY_INPUT_PII))
    assert ctx.state == FlowState.SECURITY_BLOCK
    assert ctx.security.passed is False
    assert "ssn" in ctx.security.flagged_terms
    assert "credit_card" in ctx.security.flagged_terms
    assert "salary" in ctx.security.flagged_terms


def test_rbac_violation_blocks():
    ctx = security_check(FlowContext(raw=RISKY_INPUT_RBAC))
    assert ctx.state == FlowState.SECURITY_BLOCK
    assert ctx.security.passed is False
    assert any(t in ctx.security.flagged_terms for t in ("prod-db", "finance", "payroll"))


def test_email_scraping_flagged():
    ctx = security_check(FlowContext(raw=RISKY_INPUT_EMAIL))
    assert ctx.state == FlowState.SECURITY_BLOCK
    assert "email" in ctx.security.flagged_terms
