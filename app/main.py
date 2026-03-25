import logging

from fastapi import FastAPI, Header

from app.auth import verify_token
from app.jenkins import trigger_jenkins_job
from app.parser import parse_command
from app.schemas import BotResponse, RocketChatPayload

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
        logger.warning("auth_failed")
        return BotResponse(text="Access denied")

    # 2. Parse and validate the command
    try:
        cmd = parse_command(payload.text)
    except ValueError:
        logger.info("parse_error text=%r result=rejected", payload.text)
        return BotResponse(text="Invalid command format. Use: /db <templatebases>")

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


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
