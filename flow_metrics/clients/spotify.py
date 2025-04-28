"""Spotify API client."""

import base64
from datetime import UTC, datetime, timedelta
from typing import Any, cast

from flow_metrics.http.client import HeaderAdder, HttpClient
from flow_metrics.models.spotify import (
    AlbumTracksResponse,
    ArtistAlbumsResponse,
    ArtistStats,
    ReleaseTimeline,
    SpotifyAlbum,
    SpotifyAlbumSimplified,
    SpotifyArtist,
    SpotifyError,
    SpotifyToken,
    SpotifyTrack,
)


class SpotifyClient:
    """
    Spotify API client that handles authentication and provides methods
    for accessing endpoints relevant to artist analysis.
    """

    BASE_URL = "https://api.spotify.com/v1"
    AUTH_URL = "https://accounts.spotify.com/api/token"

    def __init__(self, client_id: str, client_secret: str) -> None:
        """Initialize the Spotify client.

        Args:
            client_id: Spotify API client ID
            client_secret: Spotify API client secret
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.token: SpotifyToken | None = None

        # Create a separate HTTP client for auth requests
        self.auth_client = HttpClient(base_url="https://accounts.spotify.com")

        # Create main API client
        self.client = HttpClient(base_url=self.BASE_URL)

    def _encode_credentials(self) -> str:
        """Encode client credentials for auth header.

        Returns:
            Base64 encoded credentials
        """
        credentials = f"{self.client_id}:{self.client_secret}"
        return base64.b64encode(credentials.encode()).decode()

    def authenticate(self) -> SpotifyToken:
        """Authenticate with Spotify API using client credentials flow.

        Returns:
            Spotify token object

        Raises:
            SpotifyError: If authentication fails
        """
        if self.token and self.token.expires_at and self.token.expires_at > datetime.now(UTC):
            # Token is still valid
            return self.token

        # Prepare auth headers
        auth_header = {
            "Authorization": f"Basic {self._encode_credentials()}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        header_adder = HeaderAdder(self.auth_client, auth_header)
        header_adder.add_headers()

        # Request a new token
        try:
            response = self.auth_client.post(
                "/api/token",
                params={"grant_type": "client_credentials"},
            )

            token_data = response.json()
            # Add expires_at field
            token_data["expires_at"] = datetime.now(UTC) + timedelta(
                seconds=token_data["expires_in"],
            )

            # Create token object
            self.token = SpotifyToken(**token_data)

            # Update API client headers
            api_headers = {"Authorization": f"Bearer {self.token.access_token}"}
            header_adder = HeaderAdder(self.client, api_headers)
            header_adder.add_headers()

            return self.token

        except Exception as e:
            raise SpotifyError(f"Authentication failed: {str(e)}") from e

    def _ensure_auth(self) -> None:
        """Ensure the client is authenticated before making a request."""
        if (
            not self.token
            or not self.token.expires_at
            or self.token.expires_at <= datetime.now(UTC)
        ):
            self.authenticate()

    def search_artists(self, query: str, limit: int = 10, offset: int = 0) -> list[SpotifyArtist]:
        """Search for artists matching the query.

        Args:
            query: Search query
            limit: Maximum number of results (default: 10, max: 50)
            offset: Offset for pagination (default: 0)

        Returns:
            list of matching artists

        Raises:
            SpotifyError: If the search fails
        """
        self._ensure_auth()

        try:
            response = self.client.get(
                "/search",
                params={
                    "q": query,
                    "type": "artist",
                    "limit": min(limit, 50),  # Max 50 per Spotify API
                    "offset": offset,
                },
            )

            data = response.json()
            return [SpotifyArtist.model_validate(artist) for artist in data["artists"]["items"]]

        except Exception as e:
            raise SpotifyError(f"Artist search failed: {str(e)}") from e

    def get_artist(self, artist_id: str) -> SpotifyArtist:
        """Get detailed information about an artist by ID.

        Args:
            artist_id: Spotify artist ID

        Returns:
            Artist information

        Raises:
            SpotifyError: If getting the artist fails
        """
        self._ensure_auth()

        try:
            response = self.client.get(f"/artists/{artist_id}")
            return SpotifyArtist.model_validate(response.json())

        except Exception as e:
            raise SpotifyError(f"Failed to get artist: {str(e)}") from e

    def get_artist_albums(
        self,
        artist_id: str,
        album_types: list[str] | None = None,  # album, single, appears_on, compilation
        limit: int = 20,
        offset: int = 0,
        market: str | None = None,
    ) -> ArtistAlbumsResponse:
        """Get albums by an artist.

        Args:
            artist_id: Spotify artist ID
            album_types: list of album types to include (default: all)
            limit: Maximum number of results (default: 20, max: 50)
            offset: Offset for pagination (default: 0)
            market: Limit results to a specific market (ISO 3166-1 alpha-2 country code)

        Returns:
            Paginated response with albums

        Raises:
            SpotifyError: If getting artist albums fails
        """
        self._ensure_auth()

        params: dict[str, Any] = {
            "limit": min(limit, 50),  # Max 50 per Spotify API
            "offset": offset,
        }

        if album_types:
            params["include_groups"] = ",".join(album_types)

        if market:
            params["market"] = market

        try:
            response = self.client.get(f"/artists/{artist_id}/albums", params=params)
            return ArtistAlbumsResponse.model_validate(response.json())

        except Exception as e:
            raise SpotifyError(f"Failed to get artist albums: {str(e)}") from e

    def get_album(self, album_id: str, market: str | None = None) -> SpotifyAlbum:
        """Get detailed information about an album by ID.

        Args:
            album_id: Spotify album ID
            market: Limit results to a specific market (ISO 3166-1 alpha-2 country code)

        Returns:
            Album information

        Raises:
            SpotifyError: If getting the album fails
        """
        self._ensure_auth()

        params: dict[str, Any] = {}
        if market:
            params["market"] = market

        try:
            response = self.client.get(f"/albums/{album_id}", params=params)
            return SpotifyAlbum.model_validate(response.json())

        except Exception as e:
            raise SpotifyError(f"Failed to get album: {str(e)}") from e

    def get_album_tracks(
        self,
        album_id: str,
        limit: int = 50,
        offset: int = 0,
        market: str | None = None,
    ) -> AlbumTracksResponse:
        """Get tracks from an album.

        Args:
            album_id: Spotify album ID
            limit: Maximum number of results (default: 50, max: 50)
            offset: Offset for pagination (default: 0)
            market: Limit results to a specific market (ISO 3166-1 alpha-2 country code)

        Returns:
            Paginated response with tracks

        Raises:
            SpotifyError: If getting album tracks fails
        """
        self._ensure_auth()

        params: dict[str, Any] = {
            "limit": min(limit, 50),  # Max 50 per Spotify API
            "offset": offset,
        }

        if market:
            params["market"] = market

        try:
            response = self.client.get(f"/albums/{album_id}/tracks", params=params)
            return AlbumTracksResponse.model_validate(response.json())

        except Exception as e:
            raise SpotifyError(f"Failed to get album tracks: {str(e)}") from e

    def get_track(self, track_id: str, market: str | None = None) -> SpotifyTrack:
        """Get detailed information about a track by ID.

        Args:
            track_id: Spotify track ID
            market: Limit results to a specific market (ISO 3166-1 alpha-2 country code)

        Returns:
            Track information

        Raises:
            SpotifyError: If getting the track fails
        """
        self._ensure_auth()

        params: dict[str, Any] = {}
        if market:
            params["market"] = market

        try:
            response = self.client.get(f"/tracks/{track_id}", params=params)
            return SpotifyTrack.model_validate(response.json())

        except Exception as e:
            raise SpotifyError(f"Failed to get track: {str(e)}") from e

    def get_artist_top_tracks(self, artist_id: str, market: str = "US") -> list[SpotifyTrack]:
        """Get artist's top tracks.

        Args:
            artist_id: Spotify artist ID
            market: Market to get tracks for (ISO 3166-1 alpha-2 country code)

        Returns:
            list of top tracks

        Raises:
            SpotifyError: If getting top tracks fails
        """
        self._ensure_auth()

        try:
            response = self.client.get(
                f"/artists/{artist_id}/top-tracks",
                params={"market": market},
            )

            data = response.json()
            return [SpotifyTrack.model_validate(track) for track in data["tracks"]]

        except Exception as e:
            raise SpotifyError(f"Failed to get artist top tracks: {str(e)}") from e

    def get_related_artists(self, artist_id: str) -> list[SpotifyArtist]:
        """Get artists related to a given artist.

        Args:
            artist_id: Spotify artist ID

        Returns:
            list of related artists

        Raises:
            SpotifyError: If getting related artists fails
        """
        self._ensure_auth()

        try:
            response = self.client.get(f"/artists/{artist_id}/related-artists")
            data = response.json()
            return [SpotifyArtist.model_validate(artist) for artist in data["artists"]]

        except Exception as e:
            raise SpotifyError(f"Failed to get related artists: {str(e)}") from e

    def get_all_artist_albums(
        self,
        artist_id: str,
        album_types: list[str] | None = None,
        market: str | None = None,
    ) -> list[SpotifyAlbumSimplified]:
        """Get all albums by an artist (handles pagination automatically).

        Args:
            artist_id: Spotify artist ID
            album_types: list of album types to include (default: all)
            market: Limit results to a specific market (ISO 3166-1 alpha-2 country code)

        Returns:
            Complete list of albums

        Raises:
            SpotifyError: If getting albums fails
        """
        offset = 0
        limit = 50  # Maximum allowed by Spotify API
        all_albums: list[SpotifyAlbumSimplified] = []

        while True:
            response = self.get_artist_albums(
                artist_id=artist_id,
                album_types=album_types,
                limit=limit,
                offset=offset,
                market=market,
            )

            all_albums.extend(response.items)

            # Check if we've received all albums
            if response.next is None or len(response.items) == 0:
                break

            offset += limit

        return all_albums

    def get_all_album_tracks(
        self,
        album_id: str,
        market: str | None = None,
    ) -> list[SpotifyTrack]:
        """Get all tracks from an album (handles pagination automatically).

        Args:
            album_id: Spotify album ID
            market: Limit results to a specific market (ISO 3166-1 alpha-2 country code)

        Returns:
            Complete list of tracks

        Raises:
            SpotifyError: If getting tracks fails
        """
        offset = 0
        limit = 50  # Maximum allowed by Spotify API
        all_tracks: list[SpotifyTrack] = []

        while True:
            response = self.get_album_tracks(
                album_id=album_id,
                limit=limit,
                offset=offset,
                market=market,
            )

            # Get full track details for each track
            for track_item in response.items:
                try:
                    track = self.get_track(track_item.id, market=market)
                    all_tracks.append(track)
                except SpotifyError:
                    # If getting full track details fails, use the simplified version
                    simplified_track = cast(SpotifyTrack, track_item)
                    all_tracks.append(simplified_track)

            # Check if we've received all tracks
            if response.next is None or len(response.items) == 0:
                break

            offset += limit

        return all_tracks

    def get_artist_all_tracks(
        self,
        artist_id: str,
        album_types: list[str] | None = None,
        market: str | None = None,
    ) -> list[SpotifyTrack]:
        """Get all tracks by an artist across all their albums.

        Args:
            artist_id: Spotify artist ID
            album_types: list of album types to include (default: all)
            market: Limit results to a specific market (ISO 3166-1 alpha-2 country code)

        Returns:
            list of all tracks

        Raises:
            SpotifyError: If getting tracks fails
        """
        # Get all albums
        albums = self.get_all_artist_albums(
            artist_id=artist_id,
            album_types=album_types,
            market=market,
        )

        # Get tracks for each album
        all_tracks: list[SpotifyTrack] = []
        for album in albums:
            album_tracks = self.get_all_album_tracks(album_id=album.id, market=market)
            all_tracks.extend(album_tracks)

        return all_tracks

    def get_artist_timeline(
        self,
        artist_id: str,
        album_types: list[str] | None = None,
        market: str | None = None,
    ) -> ReleaseTimeline:
        """Get artist release timeline organized by year.

        Args:
            artist_id: Spotify artist ID
            album_types: list of album types to include (default: all)
            market: Limit results to a specific market (ISO 3166-1 alpha-2 country code)

        Returns:
            dictionary with years as keys and lists of albums as values

        Raises:
            SpotifyError: If getting timeline fails
        """
        # Get all albums
        albums = self.get_all_artist_albums(
            artist_id=artist_id,
            album_types=album_types,
            market=market,
        )

        # Organize by year
        timeline: dict[str, list[SpotifyAlbumSimplified]] = {}
        for album in albums:
            # Extract year from release date
            year = album.release_date.split("-")[0]

            if year not in timeline:
                timeline[year] = []

            timeline[year].append(album)

        # Sort years and albums within years
        sorted_timeline: dict[str, list[SpotifyAlbumSimplified]] = {}
        for year in sorted(timeline.keys()):
            # Sort albums by release date (most recent first)
            sorted_albums = sorted(
                timeline[year],
                key=lambda a: a.release_date,
                reverse=True,
            )
            sorted_timeline[year] = sorted_albums

        return ReleaseTimeline(timeline=sorted_timeline)

    def get_artist_stats(self, artist_id: str, market: str | None = None) -> ArtistStats:
        """Get comprehensive artist statistics.

        Args:
            artist_id: Spotify artist ID
            market: Limit results to a specific market (ISO 3166-1 alpha-2 country code)

        Returns:
            dictionary with artist statistics

        Raises:
            SpotifyError: If getting statistics fails
        """
        # Get artist details
        artist = self.get_artist(artist_id)

        # Get all albums by type
        albums = self.get_all_artist_albums(artist_id=artist_id, market=market)

        # Count by album type
        album_counts: dict[str, int] = {
            "album": 0,
            "single": 0,
            "compilation": 0,
            "appears_on": 0,
            "total": len(albums),
        }

        for album in albums:
            if album.album_type in album_counts:
                album_counts[album.album_type] += 1

        # Get top tracks
        top_tracks = self.get_artist_top_tracks(
            artist_id=artist_id,
            market=market or "US",
        )

        # Calculate average popularity
        avg_popularity = (
            sum(track.popularity or 0 for track in top_tracks) / len(top_tracks)
            if top_tracks
            else 0.0
        )

        return ArtistStats(
            artist=artist,
            album_counts=album_counts,
            top_tracks=top_tracks,
            average_track_popularity=avg_popularity,
            genres=artist.genres,
            followers=artist.followers.total if artist.followers else 0,
            popularity=artist.popularity,
        )
