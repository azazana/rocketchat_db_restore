from app.config import ALLOWED_TEMPLATEBASES
from app.schemas import ParsedCommand

_USAGE = "Invalid command format. Use: /db <templatebases>"


def parse_command(text: str) -> ParsedCommand:
    """Parse and validate a template restore command.

    Accepted formats: ``/db <templatebases>`` or ``<templatebases>``.

    Raises:
        ValueError: on any validation failure.
    """
    parts = text.strip().split()
    if len(parts) == 2 and parts[0].split("@", 1)[0] == "/db":
        templatebases = parts[1]
    elif len(parts) == 1:
        templatebases = parts[0]
    else:
        raise ValueError(_USAGE)

    if templatebases not in ALLOWED_TEMPLATEBASES:
        raise ValueError(
            f"Invalid templatebases {templatebases!r}. Allowed: {', '.join(sorted(ALLOWED_TEMPLATEBASES))}."
        )

    return ParsedCommand(templatebases=templatebases)
