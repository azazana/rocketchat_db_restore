from pydantic import BaseModel


class RocketChatPayload(BaseModel):
    """JSON body sent by Rocket.Chat outgoing webhook."""

    text: str


class ParsedCommand(BaseModel):
    """Validated template base extracted from the command text."""

    templatebases: str


class BotResponse(BaseModel):
    """Outgoing response returned to Rocket.Chat."""

    text: str
