"""Musixmatch API client."""

from typing import Any

from flow_metrics.http.client import HttpClient
from flow_metrics.models.musixmatch import (
    MusixmatchArtist,
    MusixmatchError,
    MusixmatchLyrics,
    MusixmatchTrack,
)


class MusixmatchClient:
    """
    Musixmatch API client that provides methods for accessing endpoints
    relevant to lyrics and artist data.
    """

    BASE_URL = "https://api.musixmatch.com/ws/1.1"

    def __init__(self, api_key: str) -> None:
        """Initialize the Musixmatch client.

        Args:
            api_key: Musixmatch API key
        """
        self.api_key = api_key
        self.client = HttpClient(base_url=self.BASE_URL)

    def _make_request(self, endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Make a request to the Musixmatch API.

        Args:
            endpoint: API endpoint
            params: Query parameters

        Returns:
            API response data

        Raises:
            MusixmatchError: If the request fails
        """
        # Add API key to params
        params = params or {}
        params["apikey"] = self.api_key

        try:
            response = self.client.get(endpoint, params=params)
            data = response.json()

            # Check for errors in response
            status_code = data.get("message", {}).get("header", {}).get("status_code", 0)
            if status_code != 200:
                error_message = (
                    data.get("message", {}).get("header", {}).get("hint", "Unknown error")
                )
                raise MusixmatchError(f"API error: {error_message}", status_code=status_code)

            return data
        except Exception as e:
            if isinstance(e, MusixmatchError):
                raise
            raise MusixmatchError(f"Request failed: {str(e)}") from e

    def search_artist(self, name: str, page: int = 1, page_size: int = 5) -> list[MusixmatchArtist]:
        """Search for artists.

        Args:
            name: Artist name to search for
            page: Page number (default: 1)
            page_size: Page size (default: 5, max: 100)

        Returns:
            List of matching artists

        Raises:
            MusixmatchError: If the search fails
        """
        params = {
            "q_artist": name,
            "page": page,
            "page_size": min(page_size, 100),
        }

        try:
            data = self._make_request("/artist.search", params)
            artist_list = data.get("message", {}).get("body", {}).get("artist_list", [])

            return [MusixmatchArtist.model_validate(item.get("artist", {})) for item in artist_list]
        except Exception as e:
            if isinstance(e, MusixmatchError):
                raise
            raise MusixmatchError(f"Artist search failed: {str(e)}") from e

    def search_tracks(
        self,
        query: str = "",
        artist_name: str = "",
        track_name: str = "",
        page: int = 1,
        page_size: int = 10,
    ) -> list[MusixmatchTrack]:
        """Search for tracks.

        Args:
            query: General search query
            artist_name: Artist name to filter by
            track_name: Track name to filter by
            page: Page number (default: 1)
            page_size: Page size (default: 10, max: 100)

        Returns:
            List of matching tracks

        Raises:
            MusixmatchError: If the search fails
        """
        params = {
            "page": page,
            "page_size": min(page_size, 100),
            "s_track_rating": "desc",  # Sort by rating
        }

        if query:
            params["q"] = query
        if artist_name:
            params["q_artist"] = artist_name
        if track_name:
            params["q_track"] = track_name

        try:
            data = self._make_request("/track.search", params)
            track_list = data.get("message", {}).get("body", {}).get("track_list", [])

            return [MusixmatchTrack.model_validate(item.get("track", {})) for item in track_list]
        except Exception as e:
            if isinstance(e, MusixmatchError):
                raise
            raise MusixmatchError(f"Track search failed: {str(e)}") from e

    def get_artist_tracks(
        self,
        artist_id: int,
        page: int = 1,
        page_size: int = 10,
    ) -> list[MusixmatchTrack]:
        """Get tracks by an artist.

        Args:
            artist_id: Musixmatch artist ID
            page: Page number (default: 1)
            page_size: Page size (default: 10, max: 100)

        Returns:
            List of tracks by the artist

        Raises:
            MusixmatchError: If getting tracks fails
        """
        params = {
            "artist_id": artist_id,
            "page": page,
            "page_size": min(page_size, 100),
            "s_track_rating": "desc",  # Sort by rating
        }

        try:
            data = self._make_request("/track.search", params)
            track_list = data.get("message", {}).get("body", {}).get("track_list", [])

            return [MusixmatchTrack.model_validate(item.get("track", {})) for item in track_list]
        except Exception as e:
            if isinstance(e, MusixmatchError):
                raise
            raise MusixmatchError(f"Failed to get artist tracks: {str(e)}") from e

    def get_track_lyrics(self, track_id: int) -> MusixmatchLyrics:
        """Get lyrics for a track.

        Args:
            track_id: Musixmatch track ID

        Returns:
            Lyrics data

        Raises:
            MusixmatchError: If getting lyrics fails
        """
        params = {
            "track_id": track_id,
        }

        try:
            data = self._make_request("/track.lyrics.get", params)
            lyrics_data = data.get("message", {}).get("body", {}).get("lyrics", {})

            return MusixmatchLyrics.model_validate(lyrics_data)
        except Exception as e:
            if isinstance(e, MusixmatchError):
                raise
            raise MusixmatchError(f"Failed to get track lyrics: {str(e)}") from e

    def get_all_artist_tracks(self, artist_id: int, limit: int = 50) -> list[MusixmatchTrack]:
        """Get all tracks by an artist (handles pagination).

        Args:
            artist_id: Musixmatch artist ID
            limit: Maximum number of tracks to retrieve

        Returns:
            List of all tracks by the artist

        Raises:
            MusixmatchError: If getting tracks fails
        """
        all_tracks: list[MusixmatchTrack] = []
        page = 1
        page_size = min(100, limit)  # Max page size is 100

        while len(all_tracks) < limit:
            tracks = self.get_artist_tracks(
                artist_id=artist_id,
                page=page,
                page_size=page_size,
            )

            all_tracks.extend(tracks)

            # Check if we've received all tracks
            if len(tracks) < page_size:
                break

            page += 1

            # Check if we've reached the limit
            if len(all_tracks) >= limit:
                all_tracks = all_tracks[:limit]
                break

        return all_tracks
