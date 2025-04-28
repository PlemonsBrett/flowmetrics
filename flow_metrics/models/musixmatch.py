"""Pydantic models for Musixmatch API responses."""

from typing import Any

from pydantic import BaseModel, Field


class MusixmatchError(Exception):
    """Custom exception for Musixmatch API errors."""

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


class MusixmatchArtist(BaseModel):
    """Musixmatch artist object."""

    artist_id: int
    artist_name: str
    artist_country: str | None = None
    artist_rating: int = 0
    artist_twitter_url: str | None = None
    artist_comment: str | None = None
    artist_name_translation_list: list[dict[str, Any]] = Field(default_factory=list)


class MusixmatchTrack(BaseModel):
    """Musixmatch track object."""

    track_id: int
    track_name: str
    track_rating: int = 0
    commontrack_id: int = 0
    has_lyrics: int = 0
    has_subtitles: int = 0
    artist_id: int
    artist_name: str
    album_id: int | None = None
    album_name: str | None = None
    track_share_url: str | None = None
    track_edit_url: str | None = None
    explicit: int = 0
    instrumental: int = 0


class MusixmatchLyrics(BaseModel):
    """Musixmatch lyrics object."""

    lyrics_id: int
    lyrics_body: str
    lyrics_copyright: str
    lyrics_language: str | None = None
    script_tracking_url: str | None = None
    pixel_tracking_url: str | None = None
    html_tracking_url: str | None = None
