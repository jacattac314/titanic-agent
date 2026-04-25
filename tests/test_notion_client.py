"""Notion client tests with HTTP mocked via responses."""
from __future__ import annotations

import json

import pytest
import responses

from titanic_agent.models import PRD
from titanic_agent.notion_client import _page_payload, create_notion_page


@pytest.fixture
def prd() -> PRD:
    return PRD(
        title="MLOps Latency Auditor",
        executive_summary="Flag high-latency models in the St. Louis region.",
        personas=["MLOps Engineer", "TPM"],
        success_metrics=["P95 < 200ms", "Alert MTTR < 15min"],
        risks=["Quota limits under burst load", "PII leakage if ticket body unsanitized"],
        api_endpoints=["GET /v1/models/{id}/latency-stats", "POST /v1/jira/issues"],
        priority="P1",
        security_tier="ELEVATED",
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


def test_page_payload_security_tier(prd):
    payload = _page_payload(prd, "db-test-123")
    assert payload["properties"]["Security Tier"] == {"select": {"name": "ELEVATED"}}


def test_page_payload_toggle_risks(prd):
    payload = _page_payload(prd, "db-test-123")
    block_types = [b["type"] for b in payload["children"]]
    assert "toggle" in block_types
    toggle = next(b for b in payload["children"] if b["type"] == "toggle")
    assert toggle["toggle"]["rich_text"][0]["text"]["content"] == "Risks"
    assert len(toggle["toggle"]["children"]) == len(prd.risks)


def test_page_payload_api_endpoints_code_block(prd):
    payload = _page_payload(prd, "db-test-123")
    code_block = next(b for b in payload["children"] if b["type"] == "code")
    content = code_block["code"]["rich_text"][0]["text"]["content"]
    for endpoint in prd.api_endpoints:
        assert endpoint in content
