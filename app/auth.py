from app.config import ALLOWED_USERS
from app.settings import settings


def verify_token(token: str) -> bool:
    """Return ``True`` if *token* matches the configured Rocket.Chat token."""
    return token == settings.RC_SLASH_TOKEN


def is_user_allowed(user_name: str) -> bool:
    """Return ``True`` if *user_name* is on the whitelist."""
    return user_name in ALLOWED_USERS
