import re

from app.config import ALLOWED_DUMPS, ALLOWED_TTLS
from app.schemas import ParsedCommand

_LABEL_RE = re.compile(r"^[a-z0-9-]{3,16}$")

_USAGE = "Invalid command format. Use: /db <label> <dump> <ttl>"


def parse_command(text: str, user_name: str, channel_id: str) -> ParsedCommand:
    """Parse and validate a /db command string.

    Format: ``/db <label> <dump> <ttl>``

    Raises:
        ValueError: on any validation failure.
    """
    parts = text.strip().split()
    if len(parts) != 4 or parts[0] != "/db":
        raise ValueError(_USAGE)

    _, label, dump, ttl = parts

    if not _LABEL_RE.match(label):
        raise ValueError(f"Invalid label {label!r}. Must match ^[a-z0-9-]{{3,16}}$.")
    if dump not in ALLOWED_DUMPS:
        raise ValueError(f"Invalid dump {dump!r}. Allowed: {', '.join(sorted(ALLOWED_DUMPS))}.")
    if ttl not in ALLOWED_TTLS:
        raise ValueError(f"Invalid ttl {ttl!r}. Allowed: {', '.join(sorted(ALLOWED_TTLS))}.")

    return ParsedCommand(label=label, dump=dump, ttl=ttl, user_name=user_name, channel_id=channel_id)
