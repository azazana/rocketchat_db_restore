import re

from app.config import ALLOWED_DUMPS
from app.schemas import ParsedCommand

_LABEL_RE = re.compile(r"^[a-z0-9-]{3,16}$")

_USAGE = "Invalid command format. Use: /db <label> <dump>"


def parse_command(text: str, user_name: str, channel_id: str) -> ParsedCommand:
    """Parse and validate a /db command string.

    Format: ``/db <label> <dump>``

    Raises:
        ValueError: on any validation failure.
    """
    parts = text.strip().split()
    if len(parts) != 3 or parts[0] != "/db":
        raise ValueError(_USAGE)

    _, label, dump = parts

    if not _LABEL_RE.match(label):
        raise ValueError(f"Invalid label {label!r}. Must match ^[a-z0-9-]{{3,16}}$.")
    if dump not in ALLOWED_DUMPS:
        raise ValueError(f"Invalid dump {dump!r}. Allowed: {', '.join(sorted(ALLOWED_DUMPS))}.")

    return ParsedCommand(label=label, dump=dump, user_name=user_name, channel_id=channel_id)
