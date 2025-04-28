"""Client factory module."""

from flow_metrics.clients.musicbrainz import MusicBrainzClient
from flow_metrics.clients.spotify import SpotifyClient
from flow_metrics.config.settings import get_settings


def create_spotify_client() -> SpotifyClient:
    """Create a Spotify client using app settings.

    Returns:
        Initialized Spotify client
    """
    settings = get_settings()
    return SpotifyClient(
        client_id=settings.spotify_client_id,
        client_secret=settings.spotify_client_secret,
    )


def create_musicbrainz_client() -> MusicBrainzClient:
    """Create a MusicBrainz client using app settings.

    Returns:
        Initialized MusicBrainz client
    """
    settings = get_settings()
    return MusicBrainzClient(
        app_name=settings.musicbrainz_app_name,
        app_version=settings.musicbrainz_version,
        contact_info=settings.musicbrainz_contact,
        rate_limit=1.0,  # Respect MusicBrainz rate limit of 1 request per second
    )
