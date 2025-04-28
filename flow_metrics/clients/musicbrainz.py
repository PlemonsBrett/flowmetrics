"""MusicBrainz API client."""

import time
from typing import Any

from flow_metrics.http.client import HeaderAdder, HttpClient
from flow_metrics.models.musicbrainz import (
    CoverArtResponse,
    MusicBrainzArtist,
    MusicBrainzArtistList,
    MusicBrainzError,
    MusicBrainzRecording,
    MusicBrainzRecordingList,
    MusicBrainzRelease,
    MusicBrainzReleaseGroup,
    MusicBrainzReleaseGroupList,
    MusicBrainzReleaseList,
    MusicBrainzWork,
    MusicBrainzWorkList,
)


class MusicBrainzClient:
    """
    MusicBrainz API client that handles rate limiting and provides methods
    for accessing endpoints relevant to artist analysis.
    """

    BASE_URL = "https://musicbrainz.org/ws/2"
    COVER_ART_URL = "https://coverartarchive.org"

    def __init__(
        self,
        app_name: str,
        app_version: str,
        contact_info: str,
        rate_limit: float = 1.0,
    ) -> None:
        """Initialize the MusicBrainz client.

        Args:
            app_name: Application name for User-Agent
            app_version: Application version for User-Agent
            contact_info: Contact information (email or URL) for User-Agent
            rate_limit: Time in seconds between requests (default: 1.0)
        """
        self.app_name = app_name
        self.app_version = app_version
        self.contact_info = contact_info
        self.rate_limit = rate_limit
        self.last_request_time: float | None = None

        # Create HTTP client with custom User-Agent
        self.user_agent = f"{app_name}/{app_version} ( {contact_info} )"
        headers = {"User-Agent": self.user_agent}

        self.client = HttpClient(base_url=self.BASE_URL)
        header_adder = HeaderAdder(self.client, headers)
        header_adder.add_headers()

        # Create separate client for Cover Art Archive
        self.cover_art_client = HttpClient(base_url=self.COVER_ART_URL)
        header_adder = HeaderAdder(self.cover_art_client, headers)
        header_adder.add_headers()

    def _respect_rate_limit(self) -> None:
        """Ensure we respect the MusicBrainz rate limit."""
        if self.last_request_time is not None:
            elapsed = time.time() - self.last_request_time
            if elapsed < self.rate_limit:
                time.sleep(self.rate_limit - elapsed)

        self.last_request_time = time.time()

    def _make_request(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make a request to the MusicBrainz API with rate limiting.

        Args:
            endpoint: API endpoint
            params: Query parameters

        Returns:
            API response as dict

        Raises:
            MusicBrainzError: If the request fails
        """
        # Add default JSON format parameter if not specified
        params = params or {}
        if "fmt" not in params:
            params["fmt"] = "json"

        # Respect rate limit
        self._respect_rate_limit()

        try:
            response = self.client.get(endpoint, params=params)
            return response.json()
        except Exception as e:
            raise MusicBrainzError(f"API request failed: {str(e)}") from e

    def search_artists(
        self,
        query: str,
        limit: int = 25,
        offset: int = 0,
        strict: bool = False,
    ) -> MusicBrainzArtistList:
        """Search for artists matching the query.

        Args:
            query: Search query
            limit: Maximum number of results (default: 25, max: 100)
            offset: Offset for pagination (default: 0)
            strict: If True, only return exact matches

        Returns:
            List of matching artists

        Raises:
            MusicBrainzError: If the search fails
        """
        params = {
            "query": query,
            "limit": min(limit, 100),
            "offset": offset,
        }

        if strict:
            params["strict"] = "true"

        try:
            data = self._make_request("/artist", params)
            return MusicBrainzArtistList.model_validate(data)
        except Exception as e:
            raise MusicBrainzError(f"Artist search failed: {str(e)}") from e

    def get_artist(
        self,
        artist_id: str,
        includes: list[str] | None = None,
    ) -> MusicBrainzArtist:
        """Get detailed information about an artist by ID.

        Args:
            artist_id: MusicBrainz artist ID
            includes: Additional information to include

        Returns:
            Artist information

        Raises:
            MusicBrainzError: If getting the artist fails
        """
        params: dict[str, Any] = {}

        if includes:
            params["inc"] = "+".join(includes)

        try:
            data = self._make_request(f"/artist/{artist_id}", params)
            return MusicBrainzArtist.model_validate(data)
        except Exception as e:
            raise MusicBrainzError(f"Failed to get artist: {str(e)}") from e

    def search_release_groups(
        self,
        query: str,
        limit: int = 25,
        offset: int = 0,
        artist_id: str | None = None,
        strict: bool = False,
    ) -> MusicBrainzReleaseGroupList:
        """Search for release groups matching the query.

        Args:
            query: Search query
            limit: Maximum number of results (default: 25, max: 100)
            offset: Offset for pagination (default: 0)
            artist_id: Filter by artist ID
            strict: If True, only return exact matches

        Returns:
            List of matching release groups

        Raises:
            MusicBrainzError: If the search fails
        """
        params: dict[str, Any] = {
            "query": query,
            "limit": min(limit, 100),
            "offset": offset,
        }

        if artist_id:
            params["artistid"] = artist_id

        if strict:
            params["strict"] = "true"

        try:
            data = self._make_request("/release-group", params)
            return MusicBrainzReleaseGroupList.model_validate(data)
        except Exception as e:
            raise MusicBrainzError(f"Release group search failed: {str(e)}") from e

    def get_release_group(
        self,
        release_group_id: str,
        includes: list[str] | None = None,
    ) -> MusicBrainzReleaseGroup:
        """Get detailed information about a release group by ID.

        Args:
            release_group_id: MusicBrainz release group ID
            includes: Additional information to include

        Returns:
            Release group information

        Raises:
            MusicBrainzError: If getting the release group fails
        """
        params: dict[str, Any] = {}

        if includes:
            params["inc"] = "+".join(includes)

        try:
            data = self._make_request(f"/release-group/{release_group_id}", params)
            return MusicBrainzReleaseGroup.model_validate(data)
        except Exception as e:
            raise MusicBrainzError(f"Failed to get release group: {str(e)}") from e

    def search_releases(
        self,
        query: str,
        limit: int = 25,
        offset: int = 0,
        artist_id: str | None = None,
        release_group_id: str | None = None,
        strict: bool = False,
    ) -> MusicBrainzReleaseList:
        """Search for releases matching the query.

        Args:
            query: Search query
            limit: Maximum number of results (default: 25, max: 100)
            offset: Offset for pagination (default: 0)
            artist_id: Filter by artist ID
            release_group_id: Filter by release group ID
            strict: If True, only return exact matches

        Returns:
            List of matching releases

        Raises:
            MusicBrainzError: If the search fails
        """
        params: dict[str, Any] = {
            "query": query,
            "limit": min(limit, 100),
            "offset": offset,
        }

        if artist_id:
            params["artistid"] = artist_id

        if release_group_id:
            params["reid"] = release_group_id

        if strict:
            params["strict"] = "true"

        try:
            data = self._make_request("/release", params)
            return MusicBrainzReleaseList.model_validate(data)
        except Exception as e:
            raise MusicBrainzError(f"Release search failed: {str(e)}") from e

    def get_release(
        self,
        release_id: str,
        includes: list[str] | None = None,
    ) -> MusicBrainzRelease:
        """Get detailed information about a release by ID.

        Args:
            release_id: MusicBrainz release ID
            includes: Additional information to include

        Returns:
            Release information

        Raises:
            MusicBrainzError: If getting the release fails
        """
        params: dict[str, Any] = {}

        if includes:
            params["inc"] = "+".join(includes)

        try:
            data = self._make_request(f"/release/{release_id}", params)
            return MusicBrainzRelease.model_validate(data)
        except Exception as e:
            raise MusicBrainzError(f"Failed to get release: {str(e)}") from e

    def search_recordings(
        self,
        query: str,
        limit: int = 25,
        offset: int = 0,
        artist_id: str | None = None,
        release_id: str | None = None,
        strict: bool = False,
    ) -> MusicBrainzRecordingList:
        """Search for recordings matching the query.

        Args:
            query: Search query
            limit: Maximum number of results (default: 25, max: 100)
            offset: Offset for pagination (default: 0)
            artist_id: Filter by artist ID
            release_id: Filter by release ID
            strict: If True, only return exact matches

        Returns:
            List of matching recordings

        Raises:
            MusicBrainzError: If the search fails
        """
        params: dict[str, Any] = {
            "query": query,
            "limit": min(limit, 100),
            "offset": offset,
        }

        if artist_id:
            params["arid"] = artist_id

        if release_id:
            params["reid"] = release_id

        if strict:
            params["strict"] = "true"

        try:
            data = self._make_request("/recording", params)
            return MusicBrainzRecordingList.model_validate(data)
        except Exception as e:
            raise MusicBrainzError(f"Recording search failed: {str(e)}") from e

    def get_recording(
        self,
        recording_id: str,
        includes: list[str] | None = None,
    ) -> MusicBrainzRecording:
        """Get detailed information about a recording by ID.

        Args:
            recording_id: MusicBrainz recording ID
            includes: Additional information to include

        Returns:
            Recording information

        Raises:
            MusicBrainzError: If getting the recording fails
        """
        params: dict[str, Any] = {}

        if includes:
            params["inc"] = "+".join(includes)

        try:
            data = self._make_request(f"/recording/{recording_id}", params)
            return MusicBrainzRecording.model_validate(data)
        except Exception as e:
            raise MusicBrainzError(f"Failed to get recording: {str(e)}") from e

    def search_works(
        self,
        query: str,
        limit: int = 25,
        offset: int = 0,
        strict: bool = False,
    ) -> MusicBrainzWorkList:
        """Search for works matching the query.

        Args:
            query: Search query
            limit: Maximum number of results (default: 25, max: 100)
            offset: Offset for pagination (default: 0)
            strict: If True, only return exact matches

        Returns:
            List of matching works

        Raises:
            MusicBrainzError: If the search fails
        """
        params: dict[str, Any] = {
            "query": query,
            "limit": min(limit, 100),
            "offset": offset,
        }

        if strict:
            params["strict"] = "true"

        try:
            data = self._make_request("/work", params)
            return MusicBrainzWorkList.model_validate(data)
        except Exception as e:
            raise MusicBrainzError(f"Work search failed: {str(e)}") from e

    def get_work(
        self,
        work_id: str,
        includes: list[str] | None = None,
    ) -> MusicBrainzWork:
        """Get detailed information about a work by ID.

        Args:
            work_id: MusicBrainz work ID
            includes: Additional information to include

        Returns:
            Work information

        Raises:
            MusicBrainzError: If getting the work fails
        """
        params: dict[str, Any] = {}

        if includes:
            params["inc"] = "+".join(includes)

        try:
            data = self._make_request(f"/work/{work_id}", params)
            return MusicBrainzWork.model_validate(data)
        except Exception as e:
            raise MusicBrainzError(f"Failed to get work: {str(e)}") from e

    def browse_artist_releases(
        self,
        artist_id: str,
        release_type: list[str] | None = None,
        release_status: list[str] | None = None,
        includes: list[str] | None = None,
        limit: int = 25,
        offset: int = 0,
    ) -> MusicBrainzReleaseList:
        """Browse releases by an artist.

        Args:
            artist_id: MusicBrainz artist ID
            release_type: Filter by release types
            release_status: Filter by release status
            includes: Additional information to include
            limit: Maximum number of results (default: 25, max: 100)
            offset: Offset for pagination (default: 0)

        Returns:
            List of releases

        Raises:
            MusicBrainzError: If browsing fails
        """
        params: dict[str, Any] = {
            "artist": artist_id,
            "limit": min(limit, 100),
            "offset": offset,
        }

        if release_type:
            params["type"] = "|".join(release_type)

        if release_status:
            params["status"] = "|".join(release_status)

        if includes:
            params["inc"] = "+".join(includes)

        try:
            data = self._make_request("/release", params)
            return MusicBrainzReleaseList.model_validate(data)
        except Exception as e:
            raise MusicBrainzError(f"Failed to browse artist releases: {str(e)}") from e

    def browse_artist_release_groups(
        self,
        artist_id: str,
        release_type: list[str] | None = None,
        includes: list[str] | None = None,
        limit: int = 25,
        offset: int = 0,
    ) -> MusicBrainzReleaseGroupList:
        """Browse release groups by an artist.

        Args:
            artist_id: MusicBrainz artist ID
            release_type: Filter by release types
            includes: Additional information to include
            limit: Maximum number of results (default: 25, max: 100)
            offset: Offset for pagination (default: 0)

        Returns:
            List of release groups

        Raises:
            MusicBrainzError: If browsing fails
        """
        params: dict[str, Any] = {
            "artist": artist_id,
            "limit": min(limit, 100),
            "offset": offset,
        }

        if release_type:
            params["type"] = "|".join(release_type)

        if includes:
            params["inc"] = "+".join(includes)

        try:
            data = self._make_request("/release-group", params)
            return MusicBrainzReleaseGroupList.model_validate(data)
        except Exception as e:
            raise MusicBrainzError(f"Failed to browse artist release groups: {str(e)}") from e

    def browse_release_recordings(
        self,
        release_id: str,
        includes: list[str] | None = None,
        limit: int = 25,
        offset: int = 0,
    ) -> MusicBrainzRecordingList:
        """Browse recordings in a release.

        Args:
            release_id: MusicBrainz release ID
            includes: Additional information to include
            limit: Maximum number of results (default: 25, max: 100)
            offset: Offset for pagination (default: 0)

        Returns:
            List of recordings

        Raises:
            MusicBrainzError: If browsing fails
        """
        params: dict[str, Any] = {
            "release": release_id,
            "limit": min(limit, 100),
            "offset": offset,
        }

        if includes:
            params["inc"] = "+".join(includes)

        try:
            data = self._make_request("/recording", params)
            return MusicBrainzRecordingList.model_validate(data)
        except Exception as e:
            raise MusicBrainzError(f"Failed to browse release recordings: {str(e)}") from e

    def get_cover_art(self, release_id: str) -> CoverArtResponse:
        """Get cover art for a release from the Cover Art Archive.

        Args:
            release_id: MusicBrainz release ID

        Returns:
            Cover art information

        Raises:
            MusicBrainzError: If getting cover art fails
        """
        # Respect rate limit
        self._respect_rate_limit()

        try:
            # The Cover Art Archive API doesn't use the /ws/2 prefix
            response = self.cover_art_client.get(f"/release/{release_id}")
            return CoverArtResponse.model_validate(response.json())
        except Exception as e:
            raise MusicBrainzError(f"Failed to get cover art: {str(e)}") from e

    def get_cover_art_front(self, release_id: str) -> str:
        """Get the URL of the front cover art for a release.

        Args:
            release_id: MusicBrainz release ID

        Returns:
            URL of the front cover image

        Raises:
            MusicBrainzError: If getting cover art fails or no front cover exists
        """
        try:
            cover_art = self.get_cover_art(release_id)

            for image in cover_art.images:
                if image.front:
                    return image.image

            raise MusicBrainzError("No front cover found")
        except Exception as e:
            raise MusicBrainzError(f"Failed to get front cover: {str(e)}") from e

    def get_artist_timeline(
        self,
        artist_id: str,
        release_types: list[str] | None = None,
    ) -> dict[str, list[MusicBrainzReleaseGroup]]:
        """Get an artist's release timeline organized by year.

        Args:
            artist_id: MusicBrainz artist ID
            release_types: Filter by release types

        Returns:
            Dictionary with years as keys and lists of release groups as values

        Raises:
            MusicBrainzError: If getting the timeline fails
        """
        # Get all release groups by the artist
        limit = 100
        offset = 0
        all_release_groups: list[MusicBrainzReleaseGroup] = []

        while True:
            release_groups = self.browse_artist_release_groups(
                artist_id=artist_id,
                release_type=release_types,
                includes=["artist-credits"],
                limit=limit,
                offset=offset,
            )

            all_release_groups.extend(release_groups.release_groups)

            # Check if we've received all release groups
            if len(release_groups.release_groups) < limit or not release_groups.release_groups:
                break

            offset += limit

        # Organize by year
        timeline: dict[str, list[MusicBrainzReleaseGroup]] = {}

        for release_group in all_release_groups:
            if not release_group.first_release_date:
                continue

            # Extract year
            year = release_group.first_release_date.split("-")[0]

            if year not in timeline:
                timeline[year] = []

            timeline[year].append(release_group)

        # Sort years and release groups within years
        sorted_timeline: dict[str, list[MusicBrainzReleaseGroup]] = {}

        for year in sorted(timeline.keys()):
            # Sort release groups by date
            sorted_release_groups = sorted(
                timeline[year],
                key=lambda rg: rg.first_release_date or "",
            )
            sorted_timeline[year] = sorted_release_groups

        return sorted_timeline

    def get_artist_info(self, artist_id: str) -> dict[str, Any]:
        """Get comprehensive artist information.

        Args:
            artist_id: MusicBrainz artist ID

        Returns:
            Dictionary with artist information

        Raises:
            MusicBrainzError: If getting artist info fails
        """
        # Get artist details
        artist = self.get_artist(
            artist_id=artist_id,
            includes=["url-rels", "aliases", "tags", "ratings"],
        )

        # Get release groups by type
        album_type_counts = {
            "album": 0,
            "single": 0,
            "ep": 0,
            "compilation": 0,
            "soundtrack": 0,
            "live": 0,
            "remix": 0,
            "other": 0,
            "total": 0,
        }

        # Get all release groups
        limit = 100
        offset = 0
        all_release_groups: list[MusicBrainzReleaseGroup] = []

        while True:
            release_groups = self.browse_artist_release_groups(
                artist_id=artist_id,
                includes=["artist-credits"],
                limit=limit,
                offset=offset,
            )

            all_release_groups.extend(release_groups.release_groups)

            # Check if we've received all release groups
            if len(release_groups.release_groups) < limit or not release_groups.release_groups:
                break

            offset += limit

        # Count by type
        for release_group in all_release_groups:
            album_type_counts["total"] += 1

            primary_type = release_group.primary_type or "other"

            if primary_type.lower() in album_type_counts:
                album_type_counts[primary_type.lower()] += 1
            else:
                album_type_counts["other"] += 1

            # Check for secondary types (e.g., compilation, live, soundtrack)
            if release_group.secondary_types:
                for secondary_type in release_group.secondary_types:
                    if secondary_type.lower() in album_type_counts:
                        album_type_counts[secondary_type.lower()] += 1

        # Compile artist info
        return {
            "artist": artist,
            "release_group_counts": album_type_counts,
            "all_release_groups": all_release_groups,
        }

    def find_similar_artists(self, artist_id: str) -> list[MusicBrainzArtist]:
        """Find artists similar to the given artist.

        Args:
            artist_id: MusicBrainz artist ID

        Returns:
            List of similar artists

        Raises:
            MusicBrainzError: If finding similar artists fails
        """
        # Get artist with relation info
        artist = self.get_artist(
            artist_id=artist_id,
            includes=["artist-rels"],
        )

        similar_artists: list[MusicBrainzArtist] = []

        # Look for similarity relationships
        if not getattr(artist, "relations", None):
            return similar_artists

        if artist.relations is not None:
            for relation in artist.relations:
                if relation.type in ["similar", "influenced by", "influence"] and relation.artist:
                    artist_data = relation.artist
                    similar_artist = MusicBrainzArtist.model_validate(artist_data)
                    similar_artists.append(similar_artist)

        return similar_artists
