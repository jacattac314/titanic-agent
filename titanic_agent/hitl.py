"""Human-in-the-loop approval gate with audit log."""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

from .models import FlowContext, FlowState

log = logging.getLogger("titanic_agent.hitl")

AUDIT_LOG = Path(os.environ.get("HITL_AUDIT_LOG", "hitl_audit.log"))


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def record_decision(ctx: FlowContext, approver: str, approved: bool, note: str = "") -> dict:
    """Persist an audit entry and mutate ctx."""
    ctx.state = FlowState.HUMAN_APPROVAL
    ctx.approver = approver
    entry = {
        "ts": _now_iso(),
        "approver": approver,
        "approved": approved,
        "prd_title": ctx.prd.title if ctx.prd else None,
        "submitter": ctx.raw.submitter if ctx.raw else None,
        "note": note,
    }
    try:
        with AUDIT_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except OSError as e:
        log.error("failed to write audit log: %s", e)
    log.info("HITL %s by %s: %s", "APPROVED" if approved else "REJECTED", approver, entry["prd_title"])
    if not approved:
        ctx.state = FlowState.FAILED
        ctx.error = f"rejected by {approver}: {note}" if note else f"rejected by {approver}"
    return entry
