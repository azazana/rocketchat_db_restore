from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Incoming webhook token (secret)
    RC_SLASH_TOKEN: str = Field(..., description="Rocket.Chat Slash Command Token")

    # Jenkins (secret)
    JENKINS_USER: str = Field(..., description="Jenkins username")
    JENKINS_TOKEN: str = Field(
        ...,
        description="Jenkins API token",
        validation_alias=AliasChoices("JENKINS_TOKEN", "JENKINS_API_TOKEN"),
    )


settings = Settings()
