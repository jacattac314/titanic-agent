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
    "security_tier must be one of STANDARD, ELEVATED, RESTRICTED based on data sensitivity. "
    "Personas and success_metrics must be short lists (3-5 items each). "
    "risks must be 2-4 concise risk statements. "
    "api_endpoints must be 1-5 REST or gRPC endpoint paths relevant to the idea. "
    "Assign a realistic tpm_lead full name."
)


def build_agent() -> Any:
    if not _HAS_PYDANTIC_AI:
        return None
    model = os.environ.get("PRD_MODEL", "google-gla:gemini-3-flash")
    try:
        return Agent(model, output_type=PRD, system_prompt=SYSTEM_PROMPT)
    except Exception:  # pragma: no cover - missing API key at import time
        return None


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
            risks=[
                "Vertex AI quota limits may throttle alerts under burst load",
                "PII leakage if Jira ticket body is not sanitized before write",
            ],
            api_endpoints=[
                "GET /v1/models/{model_id}/latency-stats",
                "POST /v1/jira/issues",
                "GET /v1/vertex/endpoints/{endpoint_id}/metrics",
            ],
            priority="P1",
            security_tier="ELEVATED",
            tpm_lead="Jack R.",
        )
        return ctx

    result = await _agent.run(text)
    ctx.prd = result.output  # type: ignore[attr-defined]
    return ctx
