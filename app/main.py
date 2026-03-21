import logging

from fastapi import FastAPI, Header

from app.auth import is_user_allowed, verify_token
from app.jenkins import trigger_jenkins_job
from app.parser import parse_command
from app.schemas import BotResponse, RocketChatPayload
from app.utils import generate_db_name

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Rocket.Chat DB Deployer")


@app.post("/rocketchat/db-command", response_model=BotResponse)
async def db_command(
    payload: RocketChatPayload,
    x_auth_token: str = Header(...),
) -> BotResponse:
    """Handle an incoming Rocket.Chat outgoing-webhook JSON request."""

    # 1. Verify the shared secret
    if not verify_token(x_auth_token):
        logger.warning("auth_failed user=%s", payload.user_name)
        return BotResponse(text="Access denied")

    # 2. Verify the user is on the whitelist
    if not is_user_allowed(payload.user_name):
        logger.warning("user_not_allowed user=%s", payload.user_name)
        return BotResponse(text="Access denied")

    # 3. Parse and validate the command
    try:
        cmd = parse_command(payload.text, payload.user_name, payload.channel_id)
    except ValueError:
        logger.info("parse_error user=%s text=%r result=rejected", payload.user_name, payload.text)
        return BotResponse(text="Invalid command format. Use: /db <label> <dump> <ttl>")

    # 4. Generate DB name from validated inputs only (never raw user input)
    db_name = generate_db_name(payload.user_name, cmd.label)

    # 5. Trigger Jenkins
    try:
        await trigger_jenkins_job(cmd, db_name)
    except Exception as exc:
        logger.error(
            "jenkins_error user=%s label=%s dump=%s ttl=%s error=%s result=error",
            cmd.user_name, cmd.label, cmd.dump, cmd.ttl, exc,
        )
        return BotResponse(text="Failed to trigger Jenkins job")

    logger.info(
        "user=%s label=%s dump=%s ttl=%s db=%s result=accepted",
        cmd.user_name, cmd.label, cmd.dump, cmd.ttl, db_name,
    )
    return BotResponse(
        text=f"Request accepted: db={db_name}, dump={cmd.dump}, ttl={cmd.ttl}"
    )


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
