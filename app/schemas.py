from pydantic import BaseModel


class RocketChatPayload(BaseModel):
    """JSON body sent by Rocket.Chat outgoing webhook."""

    user_name: str
    text: str
    channel_id: str


class ParsedCommand(BaseModel):
    """Validated, normalised parameters extracted from the /db command."""

    label: str
    dump: str
    user_name: str
    channel_id: str


class BotResponse(BaseModel):
    """Outgoing response returned to Rocket.Chat."""

    text: str
