from pydantic import BaseModel, Field


class RocketChatPayload(BaseModel):
    """JSON body sent by Rocket.Chat outgoing webhook."""

    text: str


class ParsedCommand(BaseModel):
    """Validated template base extracted from the command text."""

    templatebases: str


class BotResponse(BaseModel):
    """Outgoing response returned to Rocket.Chat."""

    text: str


class TelegramChat(BaseModel):
    """Telegram chat descriptor from incoming updates."""

    id: int


class TelegramUser(BaseModel):
    """Telegram user descriptor from incoming updates."""

    id: int


class TelegramMessage(BaseModel):
    """Telegram message fragment used by this service."""

    text: str | None = None
    chat: TelegramChat
    from_user: TelegramUser | None = Field(default=None, alias="from")


class TelegramUpdate(BaseModel):
    """Telegram webhook update payload (partial model)."""

    update_id: int
    message: TelegramMessage | None = None


class TelegramWebhookAck(BaseModel):
    """Plain acknowledgement returned to Telegram webhook calls."""

    ok: bool = True
