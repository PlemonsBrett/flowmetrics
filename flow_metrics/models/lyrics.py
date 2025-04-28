"""Models for lyrics scraper."""

from pydantic import BaseModel


class LyricsScraperError(Exception):
    """Custom exception for lyrics scraper errors."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)


class ScrapedLyrics(BaseModel):
    """Model for scraped lyrics data."""

    artist: str
    title: str
    lyrics: str
    source: str
    url: str
    album: str | None = None
    release_date: str | None = None
