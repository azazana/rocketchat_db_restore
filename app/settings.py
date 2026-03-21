from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Rocket.Chat
    RC_SLASH_TOKEN: str = Field(..., description="Rocket.Chat Slash Command Token")
    RC_ALLOWED_CHANNELS: str = Field(
        "#dev-db-requests",
        description="Comma-separated list of allowed Rocket.Chat channels",
    )
    RC_ALLOWED_USERS: str = Field(
        "",
        description="Comma-separated list of allowed Rocket.Chat usernames (empty = allow all)",
    )

    # Jenkins
    JENKINS_URL: str = Field(..., description="Jenkins base URL")
    JENKINS_USER: str = Field(..., description="Jenkins username")
    JENKINS_API_TOKEN: str = Field(..., description="Jenkins API token")

    @property
    def allowed_channels(self) -> List[str]:
        return [c.strip().lstrip("#") for c in self.RC_ALLOWED_CHANNELS.split(",") if c.strip()]

    @property
    def allowed_users(self) -> List[str]:
        return [u.strip() for u in self.RC_ALLOWED_USERS.split(",") if u.strip()]


settings = Settings()
