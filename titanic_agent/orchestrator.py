"""Titanic Agent orchestrator: Raw_Input -> Security_Check -> PRD -> HITL -> Notion -> Stitch."""
from __future__ import annotations

import logging
import time
from typing import Callable, Optional

from .hitl import record_decision
from .models import FlowContext, FlowState, RawIdea
from .notion_client import attach_stitch_link, create_notion_page
from .prd_agent import generate_prd
from .security import security_check
from .stitch import build_stitch_context

log = logging.getLogger("titanic_agent.orchestrator")

# A callable that returns (approved: bool, approver: str, note: str).
ApprovalFn = Callable[[FlowContext], tuple[bool, str, str]]


def _default_approval(ctx: FlowContext) -> tuple[bool, str, str]:
    """Auto-approve in absence of a real reviewer. Override in production."""
    return True, "default-tpm@company.com", "auto-approved (no reviewer wired)"


async def run_flow(
    idea: RawIdea,
    approval_fn: Optional[ApprovalFn] = None,
    attach_links_to_notion: bool = True,
) -> FlowContext:
    """Execute the full Titanic Agent state machine."""
    start = time.monotonic()
    ctx = FlowContext(raw=idea)

    # 1. Security
    ctx = security_check(ctx)
    if ctx.state == FlowState.SECURITY_BLOCK:
        log.warning("flow halted at security for %s", idea.submitter)
        return ctx

    # 2. PRD
    try:
        ctx = await generate_prd(ctx)
    except Exception as e:  # noqa: BLE001
        ctx.state = FlowState.FAILED
        ctx.error = f"prd generation failed: {e}"
        log.exception("PRD generation failed")
        return ctx

    # 3. Human-in-the-loop
    fn = approval_fn or _default_approval
    approved, approver, note = fn(ctx)
    record_decision(ctx, approver=approver, approved=approved, note=note)
    if ctx.state == FlowState.FAILED:
        return ctx

    # 4. Notion
    ctx.state = FlowState.NOTION_CREATE
    try:
        page_id, page_url = create_notion_page(ctx.prd)  # type: ignore[arg-type]
    except Exception as e:  # noqa: BLE001
        ctx.state = FlowState.FAILED
        ctx.error = f"notion create failed: {e}"
        return ctx
    ctx.notion_page_id = page_id
    ctx.notion_page_url = page_url

    # 5. Stitch / Studio AI
    ctx.state = FlowState.STITCH_UI_CONTEXT
    stitch = build_stitch_context(page_id)
    ctx.stitch_preview_url = stitch.stitch_preview_url
    ctx.studio_ai_url = stitch.studio_ai_url

    if attach_links_to_notion:
        try:
            attach_stitch_link(page_id, stitch.stitch_preview_url, stitch.studio_ai_url)
        except Exception as e:  # noqa: BLE001
            log.warning("failed to attach stitch link to notion page %s: %s", page_id, e)

    ctx.state = FlowState.COMPLETE
    log.info("flow complete in %.2fs page=%s", time.monotonic() - start, page_id)
    return ctx
