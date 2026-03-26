import logging
import time
from collections import OrderedDict

from fastapi import FastAPI, Header

from app.auth import verify_token
from app.config import (
    ALLOWED_TELEGRAM_FULL_ACCESS_USER_IDS,
    ALLOWED_TELEGRAM_OWN_TEMPLATEBASE_BY_USER_ID,
)
from app.jenkins import trigger_jenkins_job
from app.parser import parse_command
from app.schemas import BotResponse, RocketChatPayload, TelegramUpdate, TelegramWebhookAck
from app.settings import settings
from app.telegram import send_telegram_message

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Rocket.Chat DB Deployer")


_TELEGRAM_UPDATE_TTL_SECONDS = 3600
_TELEGRAM_DEDUP_MAX_SIZE = 10000
_seen_telegram_updates: OrderedDict[int, float] = OrderedDict()


def _is_duplicate_telegram_update(update_id: int) -> bool:
    """Return True when the Telegram update_id has already been processed recently."""
    now = time.monotonic()

    # Drop expired records first.
    while _seen_telegram_updates:
        oldest_update_id, seen_at = next(iter(_seen_telegram_updates.items()))
        if now - seen_at <= _TELEGRAM_UPDATE_TTL_SECONDS:
            break
        _seen_telegram_updates.pop(oldest_update_id)

    if update_id in _seen_telegram_updates:
        return True

    _seen_telegram_updates[update_id] = now

    # Keep memory bounded for long-lived processes.
    while len(_seen_telegram_updates) > _TELEGRAM_DEDUP_MAX_SIZE:
        _seen_telegram_updates.popitem(last=False)

    return False


@app.post("/rocketchat/db-command", response_model=BotResponse)
async def db_command(
    payload: RocketChatPayload,
    x_auth_token: str = Header(...),
) -> BotResponse:
    """Handle an incoming Rocket.Chat outgoing-webhook JSON request."""

    # 1. Verify the shared secret
    if not verify_token(x_auth_token):
        logger.warning("auth_failed")
        return BotResponse(text="Access denied")

    # 2. Parse and validate the command
    try:
        cmd = parse_command(payload.text)
    except ValueError as exc:
        logger.info("parse_error text=%r error=%s result=rejected", payload.text, exc)
        return BotResponse(text=str(exc))

    # 3. Trigger Jenkins
    try:
        await trigger_jenkins_job(cmd)
    except Exception as exc:
        logger.error(
            "jenkins_error templatebases=%s error=%s result=error",
            cmd.templatebases, exc,
        )
        return BotResponse(text="Failed to trigger Jenkins job")

    logger.info(
        "templatebases=%s result=accepted",
        cmd.templatebases,
    )
    return BotResponse(
        text=f"Request accepted: templatebases={cmd.templatebases}"
    )


@app.post("/telegram/webhook", response_model=TelegramWebhookAck)
async def telegram_webhook(
    payload: TelegramUpdate,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
) -> TelegramWebhookAck:
    """Handle incoming Telegram webhook updates."""

    if _is_duplicate_telegram_update(payload.update_id):
        logger.info("telegram_duplicate_update_ignored update_id=%s", payload.update_id)
        return TelegramWebhookAck(ok=True)

    if settings.TELEGRAM_WEBHOOK_SECRET and x_telegram_bot_api_secret_token != settings.TELEGRAM_WEBHOOK_SECRET:
        logger.warning("telegram_auth_failed update_id=%s", payload.update_id)
        return TelegramWebhookAck(ok=False)

    message = payload.message
    if not message or not message.text:
        return TelegramWebhookAck(ok=True)

    sender = message.from_user
    if message.text.strip().split("@", 1)[0] == "/whoami":
        user_id_text = str(sender.id) if sender else "unknown"
        await send_telegram_message(message.chat.id, f"Your Telegram user id: {user_id_text}")
        return TelegramWebhookAck(ok=True)

    if not sender:
        logger.warning("telegram_user_not_allowed update_id=%s user_id=None", payload.update_id)
        await send_telegram_message(message.chat.id, "Access denied")
        return TelegramWebhookAck(ok=True)

    try:
        cmd = parse_command(message.text)
    except ValueError as exc:
        logger.info(
            "telegram_parse_error update_id=%s text=%r error=%s result=rejected",
            payload.update_id,
            message.text,
            exc,
        )
        await send_telegram_message(message.chat.id, str(exc))
        return TelegramWebhookAck(ok=True)

    user_id = sender.id
    own_templatebase = ALLOWED_TELEGRAM_OWN_TEMPLATEBASE_BY_USER_ID.get(user_id)

    if user_id not in ALLOWED_TELEGRAM_FULL_ACCESS_USER_IDS:
        if own_templatebase is None:
            logger.warning("telegram_user_not_allowed update_id=%s user_id=%s", payload.update_id, user_id)
            await send_telegram_message(message.chat.id, "Access denied")
            return TelegramWebhookAck(ok=True)

        if cmd.templatebases != own_templatebase:
            logger.warning(
                "telegram_template_not_allowed update_id=%s user_id=%s requested=%s allowed=%s",
                payload.update_id,
                user_id,
                cmd.templatebases,
                own_templatebase,
            )
            await send_telegram_message(
                message.chat.id,
                f"Access denied. You can deploy only: {own_templatebase}",
            )
            return TelegramWebhookAck(ok=True)

    try:
        await trigger_jenkins_job(cmd)
        await send_telegram_message(
            message.chat.id,
            f"Request accepted: templatebases={cmd.templatebases}",
        )
    except Exception as exc:
        logger.error(
            "telegram_jenkins_error templatebases=%s error=%s result=error",
            cmd.templatebases,
            exc,
        )
        await send_telegram_message(message.chat.id, "Failed to trigger Jenkins job")

    return TelegramWebhookAck(ok=True)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
