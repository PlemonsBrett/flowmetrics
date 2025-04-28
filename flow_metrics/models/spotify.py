"""Pydantic models for Spotify API responses."""

from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

# Generic type for items in paginated responses
T = TypeVar("T")


class SpotifyToken(BaseModel):
    """Spotify API authentication token."""

    access_token: str
    token_type: str
    expires_in: int
    scope: str = ""
    expires_at: datetime | None = None


class SpotifyError(Exception):
    """Custom exception for Spotify API errors."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_data: dict[str, Any] | None = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(self.message)


class SpotifyImage(BaseModel):
    """Spotify image object."""

    url: str
    height: int | None = None
    width: int | None = None


class SpotifyFollowers(BaseModel):
    """Spotify followers object."""

    href: str | None = None
    total: int


class SpotifyExternalUrls(BaseModel):
    """External URLs for Spotify objects."""

    spotify: str = Field(alias="spotify", default="")

    class Config:
        populate_by_name = True


class SpotifyExternalIds(BaseModel):
    """External IDs for Spotify objects."""

    isrc: str | None = None
    ean: str | None = None
    upc: str | None = None


class SpotifyArtistSimplified(BaseModel):
    """Simplified Spotify artist object."""

    id: str
    name: str
    external_urls: SpotifyExternalUrls
    href: str
    type: str
    uri: str


class SpotifyArtist(SpotifyArtistSimplified):
    """Full Spotify artist object."""

    popularity: int | None = None
    genres: list[str] = Field(default_factory=list)
    followers: SpotifyFollowers | None = None
    images: list[SpotifyImage] = Field(default_factory=list)


class SpotifyAlbumSimplified(BaseModel):
    """Simplified Spotify album object."""

    id: str
    name: str
    album_type: str  # album, single, compilation
    release_date: str
    release_date_precision: str  # year, month, day
    total_tracks: int
    images: list[SpotifyImage] = Field(default_factory=list)
    artists: list[SpotifyArtistSimplified] = Field(default_factory=list)
    external_urls: SpotifyExternalUrls
    href: str
    type: str
    uri: str


class SpotifyAlbum(SpotifyAlbumSimplified):
    """Full Spotify album object."""

    genres: list[str] = Field(default_factory=list)
    label: str | None = None
    popularity: int | None = None
    copyrights: list[dict[str, str]] = Field(default_factory=list)
    external_ids: SpotifyExternalIds | None = None


class SpotifyTrackSimplified(BaseModel):
    """Simplified Spotify track object."""

    id: str
    name: str
    duration_ms: int
    explicit: bool
    artists: list[SpotifyArtistSimplified] = Field(default_factory=list)
    external_urls: SpotifyExternalUrls
    href: str
    type: str
    uri: str
    preview_url: str | None = None
    disc_number: int
    track_number: int


class SpotifyTrack(SpotifyTrackSimplified):
    """Full Spotify track object."""

    album: SpotifyAlbumSimplified | None = None
    popularity: int | None = None
    external_ids: SpotifyExternalIds | None = None
    is_playable: bool | None = None


class PaginatedResponse(BaseModel, Generic[T]):
    """Base class for paginated responses from Spotify API."""

    href: str
    items: list[T]
    limit: int
    next: str | None = None
    offset: int
    previous: str | None = None
    total: int


class ArtistAlbumsResponse(PaginatedResponse[SpotifyAlbumSimplified]):
    """Paginated response for artist albums."""

    pass


class AlbumTracksResponse(PaginatedResponse[SpotifyTrackSimplified]):
    """Paginated response for album tracks."""

    pass


class SearchResults(BaseModel):
    """Results from a Spotify search query."""

    artists: PaginatedResponse[SpotifyArtist] | None = None
    albums: PaginatedResponse[SpotifyAlbumSimplified] | None = None
    tracks: PaginatedResponse[SpotifyTrack] | None = None


class ArtistStats(BaseModel):
    """Compiled statistics for an artist."""

    artist: SpotifyArtist
    album_counts: dict[str, int]
    top_tracks: list[SpotifyTrack] = Field(default_factory=list)
    average_track_popularity: float = 0.0
    genres: list[str] = Field(default_factory=list)
    followers: int = 0
    popularity: int | None = None


class ReleaseTimeline(BaseModel):
    """Artist release timeline by year."""

    timeline: dict[str, list[SpotifyAlbumSimplified]]
