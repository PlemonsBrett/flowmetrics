"""Application configuration settings."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings.

    This class uses Pydantic to load and validate environment variables.
    """

    # Spotify API credentials
    spotify_client_id: str = Field(..., description="Spotify API client ID")
    spotify_client_secret: str = Field(..., description="Spotify API client secret")

    # MusicBrainz API settings
    musicbrainz_app_name: str = Field(
        "FlowMetrics",
        description="User-Agent app name for MusicBrainz API",
    )
    musicbrainz_version: str = Field("1.0", description="Version for MusicBrainz API User-Agent")
    musicbrainz_contact: str = Field(
        "brett.plemons@gmail.com",
        description="Contact email for MusicBrainz API User-Agent",
    )

    # Musixmatch API credentials
    musixmatch_api_key: str = Field(..., description="Musixmatch API key")

    # Application settings
    log_level: str = Field("INFO", description="Logging level")
    cache_dir: str = Field(".cache", description="Directory for caching API responses")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    def get_spotify_auth_header(self) -> dict[str, str]:
        """Get the Spotify authorization header for client credentials flow.

        Returns:
            Dict with authorization header
        """
        return {
            "client_id": self.spotify_client_id,
            "client_secret": self.spotify_client_secret,
        }

    def get_musicbrainz_user_agent(self) -> str:
        """Get the User-Agent string for MusicBrainz API.

        Returns:
            Formatted User-Agent string
        """
        return (
            f"{self.musicbrainz_app_name}/{self.musicbrainz_version} ({self.musicbrainz_contact})"
        )


@lru_cache
def get_settings() -> Settings:
    """Get application settings, cached for performance.

    Returns:
        Settings instance
    """
    return Settings()  # type: ignore
