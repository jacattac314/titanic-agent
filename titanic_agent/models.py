"""Pydantic models and FlowState enum for the Titanic Agent."""
from __future__ import annotations

from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field


class FlowState(str, Enum):
    RAW_INPUT = "raw_input"
    SECURITY_CHECK = "security_check"
    SECURITY_BLOCK = "security_block"
    PRD_GENERATION = "prd_generation"
    HUMAN_APPROVAL = "human_approval"
    NOTION_CREATE = "notion_create"
    STITCH_UI_CONTEXT = "stitch_ui_context"
    COMPLETE = "complete"
    FAILED = "failed"


class RawIdea(BaseModel):
    submitter: str
    role: str  # e.g. "tpm", "pm", "viewer"
    text: str


class SecurityResult(BaseModel):
    passed: bool
    sanitized_text: str
    flagged_terms: list[str] = Field(default_factory=list)
    reason: Optional[str] = None


class SecurityTier(str, Enum):
    STANDARD = "STANDARD"
    ELEVATED = "ELEVATED"
    RESTRICTED = "RESTRICTED"


class PRD(BaseModel):
    title: str = Field(..., description="Concise project title")
    executive_summary: str
    personas: list[str]
    success_metrics: list[str]
    risks: list[str] = Field(default_factory=list, description="Known risks and mitigations")
    api_endpoints: list[str] = Field(default_factory=list, description="Key API surfaces referenced")
    priority: Literal["P0", "P1", "P2"]
    security_tier: SecurityTier = SecurityTier.STANDARD
    tpm_lead: str


class FlowContext(BaseModel):
    state: FlowState = FlowState.RAW_INPUT
    raw: Optional[RawIdea] = None
    security: Optional[SecurityResult] = None
    prd: Optional[PRD] = None
    notion_page_id: Optional[str] = None
    notion_page_url: Optional[str] = None
    stitch_preview_url: Optional[str] = None
    studio_ai_url: Optional[str] = None
    approver: Optional[str] = None
    error: Optional[str] = None
