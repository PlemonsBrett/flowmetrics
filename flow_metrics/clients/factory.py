"""Client factory module."""
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