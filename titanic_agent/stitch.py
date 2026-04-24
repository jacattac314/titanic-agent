"""Stitch Canvas + Studio AI link builder.

In production, Stitch would be invoked via Opal's built-in integration.
This module generates deterministic URLs tied to the Notion page id so every
Studio AI link has a corresponding notion_page_id attached for traceability.
"""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class StitchContext:
    stitch_preview_url: str
    studio_ai_url: str
    notion_page_id: str


def build_stitch_context(notion_page_id: str) -> StitchContext:
    stitch_base = os.environ.get("STITCH_BASE_URL", "https://stitch.google/preview")
    studio_base = os.environ.get("STUDIO_AI_BASE_URL", "https://studio.google.com/live")
    return StitchContext(
        stitch_preview_url=f"{stitch_base}/{notion_page_id}",
        studio_ai_url=f"{studio_base}/{notion_page_id}",
        notion_page_id=notion_page_id,
    )
