"""End-to-end orchestrator tests with Notion + Stitch mocked out."""
from __future__ import annotations

import pytest

from titanic_agent import orchestrator
from titanic_agent.models import FlowState

from .fixtures import RISKY_INPUT_PII, SAFE_INPUT


@pytest.fixture(autouse=True)
def _patch_externals(monkeypatch):
    monkeypatch.setattr(
        orchestrator,
        "create_notion_page",
        lambda prd: ("page-abc-123", "https://www.notion.so/company/page-abc-123"),
    )
    monkeypatch.setattr(orchestrator, "attach_stitch_link", lambda *a, **kw: None)
    yield


async def test_happy_path_safe_input():
    ctx = await orchestrator.run_flow(SAFE_INPUT)
    assert ctx.state == FlowState.COMPLETE
    assert ctx.notion_page_id == "page-abc-123"
    assert ctx.studio_ai_url.endswith("page-abc-123"), "Studio AI link must carry notion_page_id"
    assert ctx.prd is not None and ctx.prd.priority in ("P0", "P1", "P2")


async def test_security_block_halts_flow():
    ctx = await orchestrator.run_flow(RISKY_INPUT_PII)
    assert ctx.state == FlowState.SECURITY_BLOCK
    assert ctx.notion_page_id is None
    assert ctx.studio_ai_url is None


async def test_hitl_rejection_halts_flow():
    def reject(ctx):
        return False, "sec-review@company.com", "contains questionable scope"
    ctx = await orchestrator.run_flow(SAFE_INPUT, approval_fn=reject)
    assert ctx.state == FlowState.FAILED
    assert ctx.notion_page_id is None
    assert "rejected" in (ctx.error or "")
