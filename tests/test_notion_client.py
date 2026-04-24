"""Notion client tests with HTTP mocked via responses."""
from __future__ import annotations

import pytest
import responses

from titanic_agent.models import PRD
from titanic_agent.notion_client import create_notion_page


@pytest.fixture
def prd() -> PRD:
    return PRD(
        title="MLOps Latency Auditor",
        executive_summary="Flag high-latency models in the St. Louis region.",
        personas=["MLOps Engineer", "TPM"],
        success_metrics=["P95 < 200ms", "Alert MTTR < 15min"],
        priority="P1",
        tpm_lead="Jack R.",
    )


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("NOTION_TOKEN", "secret_test")
    monkeypatch.setenv("NOTION_INNOVATION_DB_ID", "db-test-123")


@responses.activate
def test_create_page_happy(prd):
    responses.post(
        "https://api.notion.com/v1/pages",
        json={"id": "page-xyz", "url": "https://www.notion.so/company/page-xyz"},
        status=200,
    )
    page_id, url = create_notion_page(prd)
    assert page_id == "page-xyz"
    assert url.endswith("page-xyz")
    req = responses.calls[0].request
    assert "Bearer secret_test" in req.headers["Authorization"]


@responses.activate
def test_create_page_retries_then_succeeds(prd):
    responses.post("https://api.notion.com/v1/pages", status=500)
    responses.post("https://api.notion.com/v1/pages", status=500)
    responses.post(
        "https://api.notion.com/v1/pages",
        json={"id": "page-xyz", "url": "https://www.notion.so/company/page-xyz"},
        status=200,
    )
    page_id, _ = create_notion_page(prd)
    assert page_id == "page-xyz"
    assert len(responses.calls) == 3
