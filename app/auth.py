from app.settings import settings


def verify_token(token: str) -> bool:
    """Return ``True`` if *token* matches the configured Rocket.Chat token."""
    return token == settings.RC_SLASH_TOKEN
