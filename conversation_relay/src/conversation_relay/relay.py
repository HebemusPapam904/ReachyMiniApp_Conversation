"""Relay finished conversation turns to an external webhook over HTTP."""

import os
import asyncio
import logging
from datetime import datetime, timezone

import httpx


logger = logging.getLogger(__name__)

RELAY_WEBHOOK_URL_ENV = "RELAY_WEBHOOK_URL"
_TIMEOUT_S = 3.0


def send_transcript_webhook(role: str, text: str, final: bool) -> None:
    """Fire-and-forget POST of a finished transcript turn to the configured webhook.

    Schedules the request on the running event loop so the realtime conversation
    loop is never blocked or delayed by network latency. Silently logs failures
    (unreachable webhook, timeout) without retrying, per app configuration.
    """
    webhook_url = os.getenv(RELAY_WEBHOOK_URL_ENV, "").strip()
    if not webhook_url or not final:
        return

    payload = {
        "role": role,
        "text": text,
        "final": final,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    try:
        asyncio.create_task(_post(webhook_url, payload))
    except RuntimeError:
        logger.debug("No running event loop; dropping transcript webhook", exc_info=True)


async def _post(webhook_url: str, payload: dict) -> None:
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT_S) as client:
            response = await client.post(webhook_url, json=payload)
            response.raise_for_status()
    except Exception:
        logger.warning("Transcript webhook POST to %s failed", webhook_url, exc_info=True)
