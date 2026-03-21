def generate_db_name(user_name: str, label: str) -> str:
    """Generate the database name from the requesting user and the validated label.

    Format: ``db-<user_name>-<label>``

    Example: ``db-ivan-api``
    """
    return f"db-{user_name}-{label}"
