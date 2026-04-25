"""Stitch context builder tests."""
from __future__ import annotations

import pytest

from titanic_agent.stitch import StitchContext, build_stitch_context


def test_default_urls_contain_page_id():
    ctx = build_stitch_context("page-abc-123")
    assert isinstance(ctx, StitchContext)
    assert ctx.notion_page_id == "page-abc-123"
    assert ctx.stitch_preview_url.endswith("page-abc-123")
    assert ctx.studio_ai_url.endswith("page-abc-123")


def test_custom_base_urls(monkeypatch):
    monkeypatch.setenv("STITCH_BASE_URL", "https://custom-stitch.example.com/p")
    monkeypatch.setenv("STUDIO_AI_BASE_URL", "https://custom-studio.example.com/live")
    ctx = build_stitch_context("page-xyz")
    assert ctx.stitch_preview_url == "https://custom-stitch.example.com/p/page-xyz"
    assert ctx.studio_ai_url == "https://custom-studio.example.com/live/page-xyz"


def test_urls_are_distinct():
    ctx = build_stitch_context("page-001")
    assert ctx.stitch_preview_url != ctx.studio_ai_url


def test_page_id_propagated():
    ctx = build_stitch_context("notion-page-99")
    assert ctx.notion_page_id == "notion-page-99"
    assert "notion-page-99" in ctx.stitch_preview_url
    assert "notion-page-99" in ctx.studio_ai_url
