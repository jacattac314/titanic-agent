"""Notion API client with tenacity retry and Slack fallback."""
from __future__ import annotations

import logging
import os
from typing import Tuple

import requests
from tenacity import retry, stop_after_attempt, wait_exponential, RetryError

from .models import PRD

log = logging.getLogger("titanic_agent.notion")

NOTION_API = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"


def _headers() -> dict[str, str]:
    token = os.environ["NOTION_TOKEN"]
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def _alert_slack(message: str) -> None:
    webhook = os.environ.get("SLACK_ALERT_WEBHOOK")
    if not webhook:
        log.warning("no SLACK_ALERT_WEBHOOK configured; dropping alert: %s", message)
        return
    try:
        requests.post(webhook, json={"text": f":rotating_light: {message}"}, timeout=5)
    except requests.RequestException as e:
        log.error("slack alert failed: %s", e)


def _page_payload(prd: PRD, database_id: str) -> dict:
    return {
        "parent": {"database_id": database_id},
        "properties": {
            "Name": {"title": [{"text": {"content": prd.title}}]},
            "Priority": {"select": {"name": prd.priority}},
            "TPM Lead": {"select": {"name": prd.tpm_lead}},
            "Status": {"select": {"name": "Drafted"}},
            "Personas": {"multi_select": [{"name": p} for p in prd.personas]},
        },
        "children": [
            {
                "object": "block",
                "type": "heading_1",
                "heading_1": {
                    "rich_text": [{"type": "text", "text": {"content": "Project Overview"}}]
                },
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": prd.executive_summary}}]
                },
            },
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": "Success Metrics"}}]
                },
            },
            *[
                {
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [{"type": "text", "text": {"content": m}}]
                    },
                }
                for m in prd.success_metrics
            ],
        ],
    }


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def _create_page_request(payload: dict) -> dict:
    r = requests.post(
        f"{NOTION_API}/pages",
        headers=_headers(),
        json=payload,
        timeout=15,
    )
    r.raise_for_status()
    return r.json()


def create_notion_page(prd: PRD, database_id: str | None = None) -> Tuple[str, str]:
    """Create an Innovation DB page. Returns (page_id, page_url)."""
    db_id = database_id or os.environ["NOTION_INNOVATION_DB_ID"]
    payload = _page_payload(prd, db_id)
    try:
        data = _create_page_request(payload)
    except RetryError as e:
        _alert_slack(f"Notion create failed for '{prd.title}' after retries: {e}")
        raise
    except requests.RequestException as e:
        _alert_slack(f"Notion create failed for '{prd.title}': {e}")
        raise
    return data["id"], data["url"]


def attach_stitch_link(page_id: str, stitch_url: str, studio_ai_url: str) -> None:
    """Append a callout block with Stitch/Studio AI links to an existing page."""
    block = {
        "children": [
            {
                "object": "block",
                "type": "callout",
                "callout": {
                    "icon": {"emoji": "🎨"},
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": f"Stitch preview: {stitch_url}  |  Studio AI live: {studio_ai_url}",
                                "link": {"url": studio_ai_url},
                            },
                        }
                    ],
                },
            }
        ]
    }
    r = requests.patch(
        f"{NOTION_API}/blocks/{page_id}/children",
        headers=_headers(),
        json=block,
        timeout=15,
    )
    r.raise_for_status()
