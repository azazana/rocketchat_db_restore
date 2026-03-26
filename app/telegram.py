import asyncio
import logging
from collections.abc import Awaitable, Callable

import httpx

from app.schemas import TelegramUpdate
from app.settings import settings


logger = logging.getLogger(__name__)


async def send_telegram_message(chat_id: int, text: str) -> None:
    """Send a plain text message via Telegram Bot API."""
    if not settings.TELEGRAM_BOT_TOKEN:
        return

    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
    }

    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(url, json=payload)

    response.raise_for_status()


async def run_telegram_long_polling(
    on_update: Callable[[TelegramUpdate], Awaitable[None]],
) -> None:
    """Read Telegram updates via getUpdates long polling and dispatch them."""
    if not settings.TELEGRAM_BOT_TOKEN:
        return

    offset: int | None = None
    base_url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}"
    get_updates_url = f"{base_url}/getUpdates"
    delete_webhook_url = f"{base_url}/deleteWebhook"

    async with httpx.AsyncClient(timeout=40) as client:
        # Long polling conflicts with active webhook mode, so switch explicitly.
        try:
            await client.post(delete_webhook_url, params={"drop_pending_updates": False})
        except Exception as exc:
            logger.warning("telegram_delete_webhook_failed error=%s", exc)

        while True:
            params: dict[str, int | str] = {
                "timeout": 30,
                "allowed_updates": '["message"]',
            }
            if offset is not None:
                params["offset"] = offset

            try:
                response = await client.get(get_updates_url, params=params)
                payload = response.json()

                if response.status_code == 409:
                    logger.warning(
                        "telegram_long_polling_conflict status=409 description=%s",
                        payload.get("description"),
                    )
                    await client.post(delete_webhook_url, params={"drop_pending_updates": False})
                    await asyncio.sleep(3)
                    continue

                response.raise_for_status()

                if not payload.get("ok", False):
                    logger.warning("telegram_get_updates_failed payload=%s", payload)
                    await asyncio.sleep(2)
                    continue

                for raw_update in payload.get("result", []):
                    update = TelegramUpdate.model_validate(raw_update)
                    offset = update.update_id + 1
                    await on_update(update)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.exception("telegram_long_polling_error error=%s", exc)
                await asyncio.sleep(2)
