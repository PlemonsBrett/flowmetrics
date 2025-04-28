"""Lyrics scraper client for multiple websites."""

import random
import re
import time

import requests
from bs4 import BeautifulSoup
from bs4.element import Tag

from flow_metrics.models.lyrics import LyricsScraperError, ScrapedLyrics


class LyricsScraper:
    """Client for scraping lyrics from various websites."""

    def __init__(self, rate_limit: float = 2.0) -> None:
        """Initialize the lyrics scraper.

        Args:
            rate_limit: Minimum time in seconds between requests (default: 2.0)
        """
        self.rate_limit = rate_limit
        self.last_request_time: float = 0
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
        ]

    def _respect_rate_limit(self) -> None:
        """Ensure we respect the rate limit."""
        current_time = time.time()
        if self.last_request_time > 0:
            elapsed = current_time - self.last_request_time
            if elapsed < self.rate_limit:
                time.sleep(self.rate_limit - elapsed + random.uniform(0.1, 1.0))

        self.last_request_time = time.time()

    def _get_random_headers(self) -> dict[str, str]:
        """Get random browser-like headers.

        Returns:
            Headers dictionary
        """
        user_agent = random.choice(self.user_agents)

        return {
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": "https://www.google.com/",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "max-age=0",
        }

    def _make_request(self, url: str) -> str:
        """Make an HTTP request with rate limiting and random headers.

        Args:
            url: URL to request

        Returns:
            Response text

        Raises:
            LyricsScraperError: If the request fails
        """
        self._respect_rate_limit()

        try:
            headers = self._get_random_headers()
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.text
        except Exception as e:
            raise LyricsScraperError(f"Request failed: {str(e)}") from e

    def search_azlyrics(self, artist: str, title: str) -> str | None:
        """Search for lyrics on AZLyrics.

        Args:
            artist: Artist name
            title: Song title

        Returns:
            Lyrics URL if found, None otherwise
        """
        # Format artist and title for search
        artist_search = re.sub(r"[^a-zA-Z0-9]", "+", artist.lower())
        title_search = re.sub(r"[^a-zA-Z0-9]", "+", title.lower())

        search_url = f"https://search.azlyrics.com/search.php?q={artist_search}+{title_search}"

        try:
            html = self._make_request(search_url)
            soup = BeautifulSoup(html, "html.parser")

            # AZLyrics search results are in panels
            panels = soup.select(".panel")

            # Look for song results panel
            for panel in panels:
                heading = panel.select_one(".panel-heading")
                if heading and "song results" in heading.text.lower():
                    # Find the first result
                    result = panel.select_one("td a")
                    if result and "href" in result.attrs:
                        return str(result["href"])

            return None
        except Exception as e:
            print(f"AZLyrics search error: {e}")
            return None

    def get_lyrics_from_azlyrics(self, url: str) -> ScrapedLyrics:
        """Scrape lyrics from AZLyrics.

        Args:
            url: AZLyrics URL

        Returns:
            Scraped lyrics

        Raises:
            LyricsScraperError: If scraping fails
        """
        try:
            html = self._make_request(url)
            soup = BeautifulSoup(html, "html.parser")

            # Get artist and title
            title_div = soup.select_one(".ringtone")
            if not title_div:
                raise LyricsScraperError("Could not find title information")

            artist_element = soup.select_one(".lyricsh h2")
            if not artist_element:
                raise LyricsScraperError("Could not find artist information")

            artist_name = artist_element.text.strip()
            artist_name = re.sub(r"^lyrics by:", "", artist_name, flags=re.IGNORECASE).strip()

            previous_b = title_div.find_previous("b")
            if not previous_b:
                raise LyricsScraperError("Could not find song title")
            song_title = previous_b.text.strip()
            song_title = re.sub(r'^"(.*)"$', r"\1", song_title)  # Remove quotes

            # Find the lyrics div (it has no class, comes after ringtone div)
            lyrics_div = title_div.find_next_sibling("div")

            if not lyrics_div:
                raise LyricsScraperError("Could not find lyrics container")

            # Get the text and remove any script tags
            if isinstance(lyrics_div, Tag):
                for script in lyrics_div.find_all("script"):
                    if hasattr(script, "decompose"):
                        script.decompose()

            lyrics = lyrics_div.get_text().strip()

            return ScrapedLyrics(
                artist=artist_name,
                title=song_title,
                lyrics=lyrics,
                source="AZLyrics",
                url=url,
            )
        except Exception as e:
            if isinstance(e, LyricsScraperError):
                raise
            raise LyricsScraperError(f"Failed to scrape AZLyrics: {str(e)}") from e

    def search_metrolyrics(self, artist: str, title: str) -> str | None:
        """Search for lyrics on MetroLyrics.

        Args:
            artist: Artist name
            title: Song title

        Returns:
            Lyrics URL if found, None otherwise
        """
        # Format artist and title for URL
        artist_url = re.sub(r"[^a-zA-Z0-9]", "-", artist.lower()).strip("-")
        title_url = re.sub(r"[^a-zA-Z0-9]", "-", title.lower()).strip("-")

        # Construct direct URL
        url = f"https://www.metrolyrics.com/{title_url}-lyrics-{artist_url}.html"

        try:
            response = requests.head(url, headers=self._get_random_headers(), timeout=5)
            if response.status_code == 200:
                return url
            return None
        except Exception:
            return None

    def get_lyrics_from_metrolyrics(self, url: str) -> ScrapedLyrics:
        """Scrape lyrics from MetroLyrics.

        Args:
            url: MetroLyrics URL

        Returns:
            Scraped lyrics

        Raises:
            LyricsScraperError: If scraping fails
        """
        try:
            html = self._make_request(url)
            soup = BeautifulSoup(html, "html.parser")

            # Get artist and title
            title_element = soup.select_one("h1.title")
            artist_element = soup.select_one("h2.title")

            if not title_element or not artist_element:
                raise LyricsScraperError("Could not find title information")

            song_title = title_element.text.strip()
            song_title = re.sub(r" lyrics$", "", song_title, flags=re.IGNORECASE)

            artist_name = artist_element.text.strip()

            # Find lyrics paragraphs
            lyrics_divs = soup.select(".verse")

            if not lyrics_divs:
                raise LyricsScraperError("Could not find lyrics container")

            lyrics = "\n\n".join(div.get_text().strip() for div in lyrics_divs)

            return ScrapedLyrics(
                artist=artist_name,
                title=song_title,
                lyrics=lyrics,
                source="MetroLyrics",
                url=url,
            )
        except Exception as e:
            if isinstance(e, LyricsScraperError):
                raise
            raise LyricsScraperError(f"Failed to scrape MetroLyrics: {str(e)}") from e

    def search_lyrics_com(self, artist: str, title: str) -> str | None:
        """Search for lyrics on Lyrics.com.

        Args:
            artist: Artist name
            title: Song title

        Returns:
            Lyrics URL if found, None otherwise
        """
        # Format search terms
        search_terms = f"{artist} {title}".lower()
        search_url = f"https://www.lyrics.com/lyrics/{search_terms.replace(' ', '%20')}"

        try:
            html = self._make_request(search_url)
            soup = BeautifulSoup(html, "html.parser")

            # Find search results
            results = soup.select(".sec-lyric .lyric-meta-title a")

            for result in results:
                # Check if both artist and title are in the result
                result_text = result.text.lower()
                if artist.lower() in result_text and title.lower() in result_text:
                    return f"https://www.lyrics.com{result['href']}"

            return None
        except Exception:
            return None

    def get_lyrics_from_lyrics_com(self, url: str) -> ScrapedLyrics:
        """Scrape lyrics from Lyrics.com.

        Args:
            url: Lyrics.com URL

        Returns:
            Scraped lyrics

        Raises:
            LyricsScraperError: If scraping fails
        """
        try:
            html = self._make_request(url)
            soup = BeautifulSoup(html, "html.parser")

            # Get artist and title
            title_element = soup.select_one("h1.lyric-title")
            artist_element = soup.select_one("h3.lyric-artist a")

            if not title_element or not artist_element:
                raise LyricsScraperError("Could not find title information")

            song_title = title_element.text.strip()
            artist_name = artist_element.text.strip()

            # Find lyrics container
            lyrics_div = soup.select_one("#lyric-body-text")

            if not lyrics_div:
                raise LyricsScraperError("Could not find lyrics container")

            # Remove unwanted elements
            for el in lyrics_div.select(".adx, script, ins, .rtMatcher"):
                el.decompose()

            lyrics = lyrics_div.get_text().strip()

            return ScrapedLyrics(
                artist=artist_name,
                title=song_title,
                lyrics=lyrics,
                source="Lyrics.com",
                url=url,
            )
        except Exception as e:
            if isinstance(e, LyricsScraperError):
                raise
            raise LyricsScraperError(f"Failed to scrape Lyrics.com: {str(e)}") from e

    def get_song_lyrics(self, artist: str, title: str) -> ScrapedLyrics:
        """Get lyrics for a song by trying multiple sources.

        Args:
            artist: Artist name
            title: Song title

        Returns:
            Scraped lyrics

        Raises:
            LyricsScraperError: If all sources fail
        """
        # List of source search methods and their corresponding get methods
        sources = [
            (self.search_azlyrics, self.get_lyrics_from_azlyrics),
            (self.search_metrolyrics, self.get_lyrics_from_metrolyrics),
            (self.search_lyrics_com, self.get_lyrics_from_lyrics_com),
        ]

        errors: list[str] = []

        # Try each source
        for search_method, get_method in sources:
            try:
                url = search_method(artist, title)
                if url:
                    return get_method(url)
            except Exception as e:
                errors.append(str(e))

        # If all sources fail
        raise LyricsScraperError(
            f"Could not find lyrics for {artist} - {title} in any source: {'; '.join(errors)}",
        )

    def search_artist_songs(self, artist: str) -> list[tuple[str, str]]:
        """Search for songs by an artist using web search.

        Args:
            artist: Artist name

        Returns:
            List of (title, url) tuples

        Raises:
            LyricsScraperError: If the search fails
        """
        # Format artist for search
        artist_search = re.sub(r"[^a-zA-Z0-9]", "+", artist.lower())

        # AZLyrics has artist pages that list all songs
        url = f"https://search.azlyrics.com/search.php?q={artist_search}"

        try:
            html = self._make_request(url)
            soup = BeautifulSoup(html, "html.parser")

            # Look for artist matches
            panels = soup.select(".panel")
            artist_urls: list[str] = []

            for panel in panels:
                heading = panel.select_one(".panel-heading")
                if heading and "artist results" in heading.text.lower():
                    links = panel.select("td a")
                    for link in links:
                        if "href" in link.attrs and artist.lower() in link.text.lower():
                            artist_urls.append(str(link["href"]))
                    break

            if not artist_urls:
                return []

            # Get the first artist URL
            artist_url = artist_urls[0]

            # Get the artist page
            html = self._make_request(artist_url)
            soup = BeautifulSoup(html, "html.parser")

            # Find the album and song list
            album_divs = soup.select("div.album")

            songs = []
            for div in album_divs:
                # Find all song links
                links = div.find_next("div").select('a[href^="/lyrics/"]')
                for link in links:
                    title = link.text.strip()
                    url = f"https://www.azlyrics.com{link['href']}"
                    songs.append((title, url))

            return songs
        except Exception as e:
            raise LyricsScraperError(f"Failed to search artist songs: {str(e)}") from e

    def get_artist_lyrics(self, artist: str, max_songs: int = 5) -> list[ScrapedLyrics]:
        """Get lyrics for multiple songs by an artist.

        Args:
            artist: Artist name
            max_songs: Maximum number of songs to retrieve

        Returns:
            List of scraped lyrics

        Raises:
            LyricsScraperError: If getting lyrics fails
        """
        try:
            # Get song list
            song_urls = self.search_artist_songs(artist)

            if not song_urls:
                raise LyricsScraperError(f"Could not find songs for artist {artist}")

            # Limit to max_songs
            song_urls = song_urls[:max_songs]

            # Get lyrics for each song
            lyrics_list: list[ScrapedLyrics] = []
            for title, url in song_urls:
                try:
                    lyrics = self.get_lyrics_from_azlyrics(url)
                    lyrics_list.append(lyrics)
                except Exception as e:
                    print(f"Error getting lyrics for {title}: {e}")

            return lyrics_list
        except Exception as e:
            if isinstance(e, LyricsScraperError):
                raise
            raise LyricsScraperError(f"Failed to get artist lyrics: {str(e)}") from e
