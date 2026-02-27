import logging

import requests

from app.core.config import settings

logger = logging.getLogger(__name__)


def send_sandbox_order_received(order_id: str, order_status: str | None) -> None:
    if not settings.slack_webhook_url:
        return

    status_text = order_status or "Unknown"
    message = (
        f"🚀 [Amazon Sandbox Order Received]*\n"
        f" *주문번호:* `{order_id}`\n"
        f" *상태:* {status_text}\n"
    )

    try:
        response = requests.post(
            settings.slack_webhook_url,
            json={"text": message},
            timeout=10,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.warning("Failed to send Slack notification for order %s: %s", order_id, exc)
