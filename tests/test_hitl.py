"""Human-in-the-loop approval gate tests."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from titanic_agent import hitl
from titanic_agent.models import FlowContext, FlowState, PRD, RawIdea

from .fixtures import SAFE_INPUT


@pytest.fixture
def ctx_with_prd() -> FlowContext:
    return FlowContext(
        raw=SAFE_INPUT,
        prd=PRD(
            title="Test Initiative",
            executive_summary="A test.",
            personas=["TPM"],
            success_metrics=["Metric A"],
            risks=["Risk A"],
            api_endpoints=["GET /v1/test"],
            priority="P1",
            security_tier="STANDARD",
            tpm_lead="Jack R.",
        ),
    )


@pytest.fixture(autouse=True)
def _tmp_audit_log(monkeypatch, tmp_path):
    log_path = tmp_path / "hitl_audit.log"
    monkeypatch.setattr(hitl, "AUDIT_LOG", log_path)
    return log_path


def test_approval_sets_complete_state(ctx_with_prd, tmp_path):
    entry = hitl.record_decision(ctx_with_prd, approver="tpm@company.com", approved=True, note="lgtm")
    assert ctx_with_prd.state == FlowState.HUMAN_APPROVAL
    assert ctx_with_prd.approver == "tpm@company.com"
    assert entry["approved"] is True
    assert entry["prd_title"] == "Test Initiative"


def test_rejection_sets_failed_state(ctx_with_prd):
    hitl.record_decision(ctx_with_prd, approver="sec@company.com", approved=False, note="scope too broad")
    assert ctx_with_prd.state == FlowState.FAILED
    assert "rejected" in (ctx_with_prd.error or "")
    assert "sec@company.com" in (ctx_with_prd.error or "")


def test_audit_log_written(ctx_with_prd, tmp_path):
    log_path = tmp_path / "hitl_audit.log"
    hitl.AUDIT_LOG = log_path
    hitl.record_decision(ctx_with_prd, approver="tpm@company.com", approved=True)
    lines = log_path.read_text().strip().splitlines()
    assert len(lines) == 1
    row = json.loads(lines[0])
    assert row["approver"] == "tpm@company.com"
    assert row["approved"] is True
    assert row["submitter"] == SAFE_INPUT.submitter


def test_multiple_entries_appended(ctx_with_prd, tmp_path):
    log_path = tmp_path / "hitl_audit.log"
    hitl.AUDIT_LOG = log_path
    hitl.record_decision(ctx_with_prd, approver="a@co.com", approved=True)
    ctx_with_prd.state = FlowState.HUMAN_APPROVAL  # reset for second call
    hitl.record_decision(ctx_with_prd, approver="b@co.com", approved=True)
    lines = log_path.read_text().strip().splitlines()
    assert len(lines) == 2
