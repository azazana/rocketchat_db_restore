import httpx

from app.settings import settings


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
