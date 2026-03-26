import logging
import asyncio
from contextlib import suppress

from fastapi import FastAPI, Header

from app.auth import verify_token
from app.config import (
    ALLOWED_TELEGRAM_FULL_ACCESS_USER_IDS,
    ALLOWED_TELEGRAM_OWN_TEMPLATEBASE_BY_USER_ID,
)
from app.jenkins import trigger_jenkins_job
from app.parser import parse_command
from app.schemas import BotResponse, RocketChatPayload, TelegramUpdate
from app.settings import settings
from app.telegram import run_telegram_long_polling, send_telegram_message

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Rocket.Chat DB Deployer")


_telegram_polling_task: asyncio.Task | None = None


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


async def handle_telegram_update(payload: TelegramUpdate) -> None:
    """Process a single Telegram update received via long polling."""
    message = payload.message
    if not message or not message.text:
        return

    sender = message.from_user
    if message.text.strip().split("@", 1)[0] == "/whoami":
        user_id_text = str(sender.id) if sender else "unknown"
        await send_telegram_message(message.chat.id, f"Your Telegram user id: {user_id_text}")
        return

    if not sender:
        logger.warning("telegram_user_not_allowed update_id=%s user_id=None", payload.update_id)
        await send_telegram_message(message.chat.id, "Access denied")
        return

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
        return

    user_id = sender.id
    own_templatebase = ALLOWED_TELEGRAM_OWN_TEMPLATEBASE_BY_USER_ID.get(user_id)

    if user_id not in ALLOWED_TELEGRAM_FULL_ACCESS_USER_IDS:
        if own_templatebase is None:
            logger.warning("telegram_user_not_allowed update_id=%s user_id=%s", payload.update_id, user_id)
            await send_telegram_message(message.chat.id, "Access denied")
            return

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
            return

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


@app.on_event("startup")
async def startup_event() -> None:
    """Start Telegram long-polling worker when bot token is configured."""
    global _telegram_polling_task
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.info("telegram_long_polling_disabled reason=no_token")
        return

    _telegram_polling_task = asyncio.create_task(run_telegram_long_polling(handle_telegram_update))
    logger.info("telegram_long_polling_started")


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Gracefully stop Telegram long-polling worker."""
    global _telegram_polling_task
    if _telegram_polling_task is None:
        return

    _telegram_polling_task.cancel()
    with suppress(asyncio.CancelledError):
        await _telegram_polling_task
    _telegram_polling_task = None


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
