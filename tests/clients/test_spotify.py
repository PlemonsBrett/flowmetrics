"""Tests for Spotify client."""

import json
import os
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from requests import Response

from flow_metrics.clients.spotify import SpotifyClient
from flow_metrics.models.spotify import (
    SpotifyArtist,
    SpotifyError,
    SpotifyExternalUrls,
    SpotifyFollowers,
    SpotifyTrack,
)


# Helper function to load mock data from file
def load_mock_data(filename: str) -> dict[Any, Any]:
    """Load mock data from test fixtures."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    fixtures_dir = os.path.join(current_dir, "..", "fixtures")
    filepath = os.path.join(fixtures_dir, filename)

    if os.path.exists(filepath):
        with open(filepath, encoding="utf-8") as f:
            return json.load(f)
    return {}


# Ensure fixtures directory exists
def setup_fixtures_dir():
    """Create fixtures directory if it doesn't exist."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    fixtures_dir = os.path.join(current_dir, "..", "fixtures")
    os.makedirs(fixtures_dir, exist_ok=True)


class TestSpotifyClient:
    """Tests for SpotifyClient class."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test environment."""
        setup_fixtures_dir()

    @pytest.fixture
    def client(self):
        """Create a Spotify client for testing."""
        return SpotifyClient(client_id="test_client_id", client_secret="test_client_secret")

    @pytest.fixture
    def mock_token_response(self):
        """Create a mock token response."""
        response = MagicMock(spec=Response)
        response.json.return_value = {
            "access_token": "test_access_token",
            "token_type": "Bearer",
            "expires_in": 3600,
            "scope": "",
        }
        return response

    @pytest.fixture
    def mock_artist_response(self):
        """Create a mock artist response."""
        response = MagicMock(spec=Response)
        response.json.return_value = {
            "id": "test_artist_id",
            "name": "Test Artist",
            "popularity": 85,
            "type": "artist",
            "uri": "spotify:artist:test_artist_id",
            "href": "https://api.spotify.com/v1/artists/test_artist_id",
            "external_urls": {
                "spotify": "https://open.spotify.com/artist/test_artist_id",
            },
            "followers": {
                "href": None,
                "total": 12345678,
            },
            "genres": ["hip hop", "rap"],
            "images": [
                {
                    "height": 640,
                    "width": 640,
                    "url": "https://i.scdn.co/image/test_image_large",
                },
                {
                    "height": 300,
                    "width": 300,
                    "url": "https://i.scdn.co/image/test_image_medium",
                },
            ],
        }
        return response

    @pytest.fixture
    def mock_search_response(self):
        """Create a mock search response."""
        response = MagicMock(spec=Response)
        response.json.return_value = {
            "artists": {
                "href": "https://api.spotify.com/v1/search?query=test&type=artist&offset=0&limit=1",
                "items": [
                    {
                        "id": "test_artist_id",
                        "name": "Test Artist",
                        "popularity": 85,
                        "type": "artist",
                        "uri": "spotify:artist:test_artist_id",
                        "href": "https://api.spotify.com/v1/artists/test_artist_id",
                        "external_urls": {
                            "spotify": "https://open.spotify.com/artist/test_artist_id",
                        },
                        "followers": {
                            "href": None,
                            "total": 12345678,
                        },
                        "genres": ["hip hop", "rap"],
                        "images": [],
                    },
                ],
                "limit": 1,
                "next": None,
                "offset": 0,
                "previous": None,
                "total": 1,
            },
        }
        return response

    @pytest.fixture
    def mock_top_tracks_response(self):
        """Create a mock top tracks response."""
        response = MagicMock(spec=Response)
        response.json.return_value = {
            "tracks": [
                {
                    "id": "test_track_id_1",
                    "name": "Test Track 1",
                    "popularity": 90,
                    "duration_ms": 180000,
                    "explicit": True,
                    "type": "track",
                    "uri": "spotify:track:test_track_id_1",
                    "href": "https://api.spotify.com/v1/tracks/test_track_id_1",
                    "external_urls": {
                        "spotify": "https://open.spotify.com/track/test_track_id_1",
                    },
                    "disc_number": 1,
                    "track_number": 1,
                    "preview_url": "https://p.scdn.co/mp3-preview/test_track_id_1",
                    "artists": [
                        {
                            "id": "test_artist_id",
                            "name": "Test Artist",
                            "type": "artist",
                            "uri": "spotify:artist:test_artist_id",
                            "href": "https://api.spotify.com/v1/artists/test_artist_id",
                            "external_urls": {
                                "spotify": "https://open.spotify.com/artist/test_artist_id",
                            },
                        },
                    ],
                },
            ],
        }
        return response

    @pytest.fixture
    def mock_artist_albums_response(self):
        """Create a mock artist albums response."""
        response = MagicMock(spec=Response)
        response.json.return_value = {
            "href": "https://api.spotify.com/v1/artists/test_artist_id/albums?offset=0&limit=2",
            "items": [
                {
                    "id": "test_album_id_1",
                    "name": "Test Album 1",
                    "album_type": "album",
                    "release_date": "2022-01-01",
                    "release_date_precision": "day",
                    "total_tracks": 12,
                    "type": "album",
                    "uri": "spotify:album:test_album_id_1",
                    "href": "https://api.spotify.com/v1/albums/test_album_id_1",
                    "external_urls": {
                        "spotify": "https://open.spotify.com/album/test_album_id_1",
                    },
                    "images": [
                        {
                            "height": 640,
                            "width": 640,
                            "url": "https://i.scdn.co/image/test_album_1_large",
                        },
                    ],
                    "artists": [
                        {
                            "id": "test_artist_id",
                            "name": "Test Artist",
                            "type": "artist",
                            "uri": "spotify:artist:test_artist_id",
                            "href": "https://api.spotify.com/v1/artists/test_artist_id",
                            "external_urls": {
                                "spotify": "https://open.spotify.com/artist/test_artist_id",
                            },
                        },
                    ],
                },
                {
                    "id": "test_album_id_2",
                    "name": "Test Album 2",
                    "album_type": "single",
                    "release_date": "2021-06-15",
                    "release_date_precision": "day",
                    "total_tracks": 1,
                    "type": "album",
                    "uri": "spotify:album:test_album_id_2",
                    "href": "https://api.spotify.com/v1/albums/test_album_id_2",
                    "external_urls": {
                        "spotify": "https://open.spotify.com/album/test_album_id_2",
                    },
                    "images": [
                        {
                            "height": 640,
                            "width": 640,
                            "url": "https://i.scdn.co/image/test_album_2_large",
                        },
                    ],
                    "artists": [
                        {
                            "id": "test_artist_id",
                            "name": "Test Artist",
                            "type": "artist",
                            "uri": "spotify:artist:test_artist_id",
                            "href": "https://api.spotify.com/v1/artists/test_artist_id",
                            "external_urls": {
                                "spotify": "https://open.spotify.com/artist/test_artist_id",
                            },
                        },
                    ],
                },
            ],
            "limit": 2,
            "next": None,
            "offset": 0,
            "previous": None,
            "total": 2,
        }
        return response

    @pytest.fixture
    def mock_album_tracks_response(self):
        """Create a mock album tracks response."""
        response = MagicMock(spec=Response)
        response.json.return_value = {
            "href": "https://api.spotify.com/v1/albums/test_album_id_1/tracks?offset=0&limit=2",
            "items": [
                {
                    "id": "test_track_id_1",
                    "name": "Test Track 1",
                    "duration_ms": 180000,
                    "explicit": True,
                    "type": "track",
                    "uri": "spotify:track:test_track_id_1",
                    "href": "https://api.spotify.com/v1/tracks/test_track_id_1",
                    "external_urls": {
                        "spotify": "https://open.spotify.com/track/test_track_id_1",
                    },
                    "disc_number": 1,
                    "track_number": 1,
                    "preview_url": "https://p.scdn.co/mp3-preview/test_track_id_1",
                    "artists": [
                        {
                            "id": "test_artist_id",
                            "name": "Test Artist",
                            "type": "artist",
                            "uri": "spotify:artist:test_artist_id",
                            "href": "https://api.spotify.com/v1/artists/test_artist_id",
                            "external_urls": {
                                "spotify": "https://open.spotify.com/artist/test_artist_id",
                            },
                        },
                    ],
                },
                {
                    "id": "test_track_id_2",
                    "name": "Test Track 2",
                    "duration_ms": 240000,
                    "explicit": False,
                    "type": "track",
                    "uri": "spotify:track:test_track_id_2",
                    "href": "https://api.spotify.com/v1/tracks/test_track_id_2",
                    "external_urls": {
                        "spotify": "https://open.spotify.com/track/test_track_id_2",
                    },
                    "disc_number": 1,
                    "track_number": 2,
                    "preview_url": "https://p.scdn.co/mp3-preview/test_track_id_2",
                    "artists": [
                        {
                            "id": "test_artist_id",
                            "name": "Test Artist",
                            "type": "artist",
                            "uri": "spotify:artist:test_artist_id",
                            "href": "https://api.spotify.com/v1/artists/test_artist_id",
                            "external_urls": {
                                "spotify": "https://open.spotify.com/artist/test_artist_id",
                            },
                        },
                    ],
                },
            ],
            "limit": 2,
            "next": None,
            "offset": 0,
            "previous": None,
            "total": 2,
        }
        return response

    @patch("flow_metrics.http.client.HttpClient.post")
    def test_authenticate(
        self,
        mock_post: MagicMock,
        client: MagicMock,
        mock_token_response: MagicMock,
    ):
        """Test authentication."""
        # Setup
        mock_post.return_value = mock_token_response

        # Execute
        token = client.authenticate()

        # Assert
        assert token.access_token == "test_access_token"
        assert token.token_type == "Bearer"
        assert token.expires_in == 3600
        assert token.expires_at is not None
        mock_post.assert_called_once_with(
            "/api/token",
            params={"grant_type": "client_credentials"},
        )

    @patch("flow_metrics.clients.spotify.SpotifyClient.authenticate")
    @patch("flow_metrics.http.client.HttpClient.get")
    def test_get_artist(
        self,
        mock_get: MagicMock,
        mock_authenticate: MagicMock,
        client: MagicMock,
        mock_artist_response: MagicMock,
    ):
        """Test getting artist details."""
        # Setup
        mock_get.return_value = mock_artist_response

        # Execute
        artist = client.get_artist("test_artist_id")

        # Assert
        assert artist.id == "test_artist_id"
        assert artist.name == "Test Artist"
        assert artist.popularity == 85
        assert "hip hop" in artist.genres
        assert artist.followers.total == 12345678
        mock_authenticate.assert_called_once()
        mock_get.assert_called_once_with("/artists/test_artist_id")

    @patch("flow_metrics.clients.spotify.SpotifyClient.authenticate")
    @patch("flow_metrics.http.client.HttpClient.get")
    def test_search_artists(
        self,
        mock_get: MagicMock,
        mock_authenticate: MagicMock,
        client: MagicMock,
        mock_search_response: MagicMock,
    ):
        """Test searching for artists."""
        # Setup
        mock_get.return_value = mock_search_response

        # Execute
        artists = client.search_artists("test")

        # Assert
        assert len(artists) == 1
        assert artists[0].id == "test_artist_id"
        assert artists[0].name == "Test Artist"
        mock_authenticate.assert_called_once()
        mock_get.assert_called_once_with(
            "/search",
            params={
                "q": "test",
                "type": "artist",
                "limit": 10,
                "offset": 0,
            },
        )

    @patch("flow_metrics.clients.spotify.SpotifyClient.authenticate")
    @patch("flow_metrics.http.client.HttpClient.get")
    def test_get_artist_top_tracks(
        self,
        mock_get: MagicMock,
        mock_authenticate: MagicMock,
        client: MagicMock,
        mock_top_tracks_response: MagicMock,
    ):
        """Test getting artist top tracks."""
        # Setup
        mock_get.return_value = mock_top_tracks_response

        # Execute
        tracks = client.get_artist_top_tracks("test_artist_id")

        # Assert
        assert len(tracks) == 1
        assert tracks[0].id == "test_track_id_1"
        assert tracks[0].name == "Test Track 1"
        assert tracks[0].popularity == 90
        assert tracks[0].explicit is True
        mock_authenticate.assert_called_once()
        mock_get.assert_called_once_with(
            "/artists/test_artist_id/top-tracks",
            params={"market": "US"},
        )

    @patch("flow_metrics.clients.spotify.SpotifyClient.authenticate")
    @patch("flow_metrics.http.client.HttpClient.get")
    def test_get_artist_albums(
        self,
        mock_get: MagicMock,
        mock_authenticate: MagicMock,
        client: MagicMock,
        mock_artist_albums_response: MagicMock,
    ):
        """Test getting artist albums."""
        # Setup
        mock_get.return_value = mock_artist_albums_response

        # Execute
        albums_response = client.get_artist_albums("test_artist_id")

        # Assert
        assert albums_response.total == 2
        assert len(albums_response.items) == 2
        assert albums_response.items[0].id == "test_album_id_1"
        assert albums_response.items[0].name == "Test Album 1"
        assert albums_response.items[0].album_type == "album"
        assert albums_response.items[1].id == "test_album_id_2"
        assert albums_response.items[1].name == "Test Album 2"
        assert albums_response.items[1].album_type == "single"
        mock_authenticate.assert_called_once()
        mock_get.assert_called_once_with(
            "/artists/test_artist_id/albums",
            params={
                "limit": 20,
                "offset": 0,
            },
        )

    @patch("flow_metrics.clients.spotify.SpotifyClient.authenticate")
    @patch("flow_metrics.http.client.HttpClient.get")
    def test_get_artist_albums_with_album_types(
        self,
        mock_get: MagicMock,
        mock_authenticate: MagicMock,
        client: MagicMock,
        mock_artist_albums_response: MagicMock,
    ):
        """Test getting artist albums with album types filter."""
        # Setup
        mock_get.return_value = mock_artist_albums_response
        album_types = ["album", "single"]

        # Execute
        client.get_artist_albums("test_artist_id", album_types=album_types)

        # Assert
        mock_authenticate.assert_called_once()
        mock_get.assert_called_once_with(
            "/artists/test_artist_id/albums",
            params={
                "limit": 20,
                "offset": 0,
                "include_groups": "album,single",
            },
        )

    @patch("flow_metrics.clients.spotify.SpotifyClient.authenticate")
    @patch("flow_metrics.http.client.HttpClient.get")
    def test_get_album_tracks(
        self,
        mock_get: MagicMock,
        mock_authenticate: MagicMock,
        client: MagicMock,
        mock_album_tracks_response: MagicMock,
    ):
        """Test getting album tracks."""
        # Setup
        mock_get.return_value = mock_album_tracks_response

        # Execute
        tracks_response = client.get_album_tracks("test_album_id_1")

        # Assert
        assert tracks_response.total == 2
        assert len(tracks_response.items) == 2
        assert tracks_response.items[0].id == "test_track_id_1"
        assert tracks_response.items[0].name == "Test Track 1"
        assert tracks_response.items[1].id == "test_track_id_2"
        assert tracks_response.items[1].name == "Test Track 2"
        mock_authenticate.assert_called_once()
        mock_get.assert_called_once_with(
            "/albums/test_album_id_1/tracks",
            params={
                "limit": 50,
                "offset": 0,
            },
        )

    @patch("flow_metrics.clients.spotify.SpotifyClient.get_artist")
    @patch("flow_metrics.clients.spotify.SpotifyClient.get_all_artist_albums")
    @patch("flow_metrics.clients.spotify.SpotifyClient.get_artist_top_tracks")
    def test_get_artist_stats(
        self,
        mock_top_tracks: MagicMock,
        mock_all_albums: MagicMock,
        mock_get_artist: MagicMock,
        client: MagicMock,
    ):
        """Test getting artist statistics."""
        # Setup
        artist = SpotifyArtist(
            id="test_artist_id",
            name="Test Artist",
            popularity=85,
            genres=["hip hop", "rap"],
            followers=SpotifyFollowers(href=None, total=12345678),
            images=[],
            external_urls=SpotifyExternalUrls(
                spotify="https://open.spotify.com/artist/test_artist_id",
            ),
            href="https://api.spotify.com/v1/artists/test_artist_id",
            type="artist",
            uri="spotify:artist:test_artist_id",
        )
        mock_get_artist.return_value = artist

        albums: list[dict[str, Any]] = [
            {
                "id": "test_album_id_1",
                "name": "Test Album 1",
                "album_type": "album",
                "release_date": "2022-01-01",
                "release_date_precision": "day",
                "total_tracks": 12,
                "type": "album",
                "uri": "spotify:album:test_album_id_1",
                "href": "https://api.spotify.com/v1/albums/test_album_id_1",
                "external_urls": {
                    "spotify": "https://open.spotify.com/album/test_album_id_1",
                },
                "images": [],
                "artists": [],
            },
            {
                "id": "test_album_id_2",
                "name": "Test Album 2",
                "album_type": "single",
                "release_date": "2021-06-15",
                "release_date_precision": "day",
                "total_tracks": 1,
                "type": "album",
                "uri": "spotify:album:test_album_id_2",
                "href": "https://api.spotify.com/v1/albums/test_album_id_2",
                "external_urls": {
                    "spotify": "https://open.spotify.com/album/test_album_id_2",
                },
                "images": [],
                "artists": [],
            },
        ]
        mock_all_albums.return_value = [SpotifyArtist.model_validate(album) for album in albums]

        top_tracks: list[dict[str, Any]] = [
            {
                "id": "test_track_id_1",
                "name": "Test Track 1",
                "popularity": 90,
                "duration_ms": 180000,
                "explicit": True,
                "disc_number": 1,
                "track_number": 1,
                "preview_url": "https://p.scdn.co/mp3-preview/test_track_id_1",
                "type": "track",
                "uri": "spotify:track:test_track_id_1",
                "href": "https://api.spotify.com/v1/tracks/test_track_id_1",
                "external_urls": {
                    "spotify": "https://open.spotify.com/track/test_track_id_1",
                },
                "artists": [],
            },
        ]
        mock_top_tracks.return_value = [SpotifyTrack.model_validate(track) for track in top_tracks]

        # Execute
        stats = client.get_artist_stats("test_artist_id")

        # Assert
        assert stats.artist.id == "test_artist_id"
        assert stats.artist.name == "Test Artist"
        assert stats.album_counts["album"] == 1
        assert stats.album_counts["single"] == 1
        assert stats.album_counts["total"] == 2
        assert len(stats.top_tracks) == 1
        assert stats.average_track_popularity == 90.0
        assert "hip hop" in stats.genres
        assert stats.followers == 12345678
        assert stats.popularity == 85
        mock_get_artist.assert_called_once_with("test_artist_id")
        mock_all_albums.assert_called_once_with(
            artist_id="test_artist_id",
            market=None,
        )
        mock_top_tracks.assert_called_once_with(
            artist_id="test_artist_id",
            market="US",
        )

    @patch("flow_metrics.clients.spotify.SpotifyClient.authenticate")
    @patch("flow_metrics.http.client.HttpClient.get")
    def test_error_handling(
        self,
        mock_get: MagicMock,
        mock_authenticate: MagicMock,
        client: MagicMock,
    ):
        """Test error handling."""
        # Setup
        mock_get.side_effect = Exception("API Error")

        # Execute and Assert
        with pytest.raises(SpotifyError) as excinfo:
            client.get_artist("test_artist_id")

        assert "Failed to get artist: API Error" in str(excinfo.value)
        mock_authenticate.assert_called_once()
