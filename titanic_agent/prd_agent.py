"""PRD generation agent (PydanticAI / Gemini 3)."""
from __future__ import annotations

import os
from typing import Any

from .models import PRD, FlowContext, FlowState

try:
    from pydantic_ai import Agent  # type: ignore
    _HAS_PYDANTIC_AI = True
except Exception:  # pragma: no cover - fallback for envs without pydantic_ai
    _HAS_PYDANTIC_AI = False
    Agent = Any  # type: ignore


SYSTEM_PROMPT = (
    "You are a Senior TPM. Convert a raw product idea into a formal PRD JSON. "
    "Be concise and measurable. Priority must be one of P0, P1, P2. "
    "Personas and success_metrics must be short lists (3-5 items each). "
    "Assign a realistic tpm_lead full name."
)


def build_agent() -> Any:
    if not _HAS_PYDANTIC_AI:
        return None
    model = os.environ.get("PRD_MODEL", "google-gla:gemini-3-pro")
    return Agent(model, output_type=PRD, system_prompt=SYSTEM_PROMPT)


_agent = build_agent()


async def generate_prd(ctx: FlowContext) -> FlowContext:
    """Run the PRD agent on the sanitized idea and attach the PRD to ctx."""
    ctx.state = FlowState.PRD_GENERATION
    assert ctx.security is not None and ctx.security.passed, "security must pass first"
    text = ctx.security.sanitized_text

    if _agent is None:
        # Deterministic offline fallback for tests / local dev.
        ctx.prd = PRD(
            title=text[:60] or "Untitled Initiative",
            executive_summary=text or "No summary provided.",
            personas=["MLOps Engineer", "TPM", "Data Platform Lead"],
            success_metrics=[
                "P95 inference latency < 200ms",
                "Alert MTTR < 15min",
                "Model drift detection coverage > 90%",
            ],
            priority="P1",
            tpm_lead="Jack R.",
        )
        return ctx

    result = await _agent.run(text)
    ctx.prd = result.output  # type: ignore[attr-defined]
    return ctx
