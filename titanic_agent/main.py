"""Opal entrypoint. Produces the 'success' JSON the Opal app returns."""
from __future__ import annotations

import asyncio
import json
import logging
import time

from dotenv import load_dotenv

from .models import FlowContext, FlowState, RawIdea
from .orchestrator import run_flow

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")


def to_opal_response(ctx: FlowContext, duration_ms: int) -> dict:
    if ctx.state == FlowState.SECURITY_BLOCK:
        return {
            "status": "security_block",
            "flow_id": "titanic-agent-v1",
            "reason": ctx.security.reason if ctx.security else "blocked",
            "flagged_terms": ctx.security.flagged_terms if ctx.security else [],
        }
    if ctx.state == FlowState.FAILED:
        return {"status": "failed", "flow_id": "titanic-agent-v1", "error": ctx.error}
    return {
        "status": "success",
        "flow_id": "titanic-agent-v1",
        "human_in_the_loop": {
            "approved": True,
            "approver": ctx.approver,
            "log_reference": f"audit://hitl/{ctx.notion_page_id}",
        },
        "artifacts": {
            "notion_page_id": ctx.notion_page_id,
            "notion_page_url": ctx.notion_page_url,
            "stitch_preview_url": ctx.stitch_preview_url,
            "studio_ai_link": {
                "url": ctx.studio_ai_url,
                "notion_page_id": ctx.notion_page_id,
            },
        },
        "prd_summary": {
            "title": ctx.prd.title if ctx.prd else None,
            "priority": ctx.prd.priority if ctx.prd else None,
            "tpm_lead": ctx.prd.tpm_lead if ctx.prd else None,
        },
        "trace": {
            "states": [
                "raw_input", "security_check", "prd_generation",
                "human_approval", "notion_create", "stitch_ui_context", "complete",
            ],
            "duration_ms": duration_ms,
        },
    }


async def handle(idea_text: str, submitter: str = "demo@company.com", role: str = "tpm") -> dict:
    idea = RawIdea(submitter=submitter, role=role, text=idea_text)
    t0 = time.monotonic()
    ctx = await run_flow(idea)
    return to_opal_response(ctx, int((time.monotonic() - t0) * 1000))


def main() -> None:
    demo = (
        "Build an automated auditor for our MLOps pipeline that flags "
        "high-latency models in St. Louis."
    )
    result = asyncio.run(handle(demo))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
