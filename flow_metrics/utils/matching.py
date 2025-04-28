"""Utilities for matching entities between different music APIs."""

import re
from difflib import SequenceMatcher
from typing import Any

from flow_metrics.clients.musicbrainz import MusicBrainzClient
from flow_metrics.clients.spotify import SpotifyClient
from flow_metrics.models.musicbrainz import (
    MusicBrainzArtist,
    MusicBrainzRelease,
    MusicBrainzReleaseGroup,
)
from flow_metrics.models.spotify import SpotifyAlbum, SpotifyArtist, SpotifyTrack


def normalize_name(name: str) -> str:
    """Normalize a name for comparison.

    Args:
        name: Name to normalize

    Returns:
        Normalized name
    """
    # Convert to lowercase
    name = name.lower()

    # Remove special characters and extra whitespace
    name = re.sub(r"[^\w\s]", "", name)
    return re.sub(r"\s+", " ", name).strip()


def name_similarity(name1: str, name2: str) -> float:
    """Calculate similarity between two names.

    Args:
        name1: First name
        name2: Second name

    Returns:
        Similarity score (0-1)
    """
    # Normalize names
    name1 = normalize_name(name1)
    name2 = normalize_name(name2)

    # Calculate similarity
    return SequenceMatcher(None, name1, name2).ratio()


def find_musicbrainz_artist(
    spotify_artist: SpotifyArtist,
    mb_client: MusicBrainzClient,
    similarity_threshold: float = 0.85,
) -> MusicBrainzArtist | None:
    """Find a MusicBrainz artist matching a Spotify artist.

    Args:
        spotify_artist: Spotify artist
        mb_client: MusicBrainz client
        similarity_threshold: Minimum name similarity to consider a match

    Returns:
        Matching MusicBrainz artist or None if no match found
    """
    # Search for artist by name
    results = mb_client.search_artists(spotify_artist.name)

    if not results.artists:
        return None

    # Look for a match with high similarity
    best_match = None
    best_score = 0.0

    for mb_artist in results.artists:
        score = name_similarity(spotify_artist.name, mb_artist.name)

        if score > best_score:
            best_score = score
            best_match = mb_artist

    # Return the best match if it meets the threshold
    if best_match and best_score >= similarity_threshold:
        return best_match

    return None


def find_musicbrainz_release(
    spotify_album: SpotifyAlbum,
    mb_client: MusicBrainzClient,
    artist_id: str | None = None,
    similarity_threshold: float = 0.85,
) -> MusicBrainzRelease | None:
    """Find a MusicBrainz release matching a Spotify album.

    Args:
        spotify_album: Spotify album
        mb_client: MusicBrainz client
        artist_id: Optional MusicBrainz artist ID to filter results
        similarity_threshold: Minimum title similarity to consider a match

    Returns:
        Matching MusicBrainz release or None if no match found
    """
    # Search for release by title
    query = spotify_album.name

    if artist_id:
        results = mb_client.search_releases(query, artist_id=artist_id)
    else:
        results = mb_client.search_releases(query)

    if not results.releases:
        return None

    # Look for a match with high similarity
    best_match = None
    best_score = 0.0

    for mb_release in results.releases:
        score = name_similarity(spotify_album.name, mb_release.title)

        if score > best_score:
            best_score = score
            best_match = mb_release

    # Return the best match if it meets the threshold
    if best_match and best_score >= similarity_threshold:
        return best_match

    return None


def find_musicbrainz_release_group(
    spotify_album: SpotifyAlbum,
    mb_client: MusicBrainzClient,
    artist_id: str | None = None,
    similarity_threshold: float = 0.85,
) -> MusicBrainzReleaseGroup | None:
    """Find a MusicBrainz release group matching a Spotify album.

    Args:
        spotify_album: Spotify album
        mb_client: MusicBrainz client
        artist_id: Optional MusicBrainz artist ID to filter results
        similarity_threshold: Minimum title similarity to consider a match

    Returns:
        Matching MusicBrainz release group or None if no match found
    """
    # Search for release group by title
    query = spotify_album.name

    if artist_id:
        results = mb_client.search_release_groups(query, artist_id=artist_id)
    else:
        results = mb_client.search_release_groups(query)

    if not results.release_groups:
        return None

    # Look for a match with high similarity
    best_match = None
    best_score = 0.0

    for mb_release_group in results.release_groups:
        score = name_similarity(spotify_album.name, mb_release_group.title)

        if score > best_score:
            best_score = score
            best_match = mb_release_group

    # Return the best match if it meets the threshold
    if best_match and best_score >= similarity_threshold:
        return best_match

    return None


def find_track_matches(
    spotify_tracks: list[SpotifyTrack],
    mb_client: MusicBrainzClient,
    artist_id: str | None = None,
    similarity_threshold: float = 0.85,
) -> dict[str, dict[str, Any]]:
    """Find MusicBrainz recordings matching Spotify tracks.

    Args:
        spotify_tracks: List of Spotify tracks
        mb_client: MusicBrainz client
        artist_id: Optional MusicBrainz artist ID to filter results
        similarity_threshold: Minimum title similarity to consider a match

    Returns:
        Dictionary mapping Spotify track IDs to matching MusicBrainz recordings
    """
    matches: dict[str, dict[str, Any]] = {}

    for track in spotify_tracks:
        # Search for recording by title
        query = track.name

        if artist_id:
            results = mb_client.search_recordings(query, artist_id=artist_id)
        else:
            results = mb_client.search_recordings(query)

        if not results.recordings:
            continue

        # Look for a match with high similarity
        best_match = None
        best_score = 0.0

        for mb_recording in results.recordings:
            score = name_similarity(track.name, mb_recording.title)

            if score > best_score:
                best_score = score
                best_match = mb_recording

        # Add the best match if it meets the threshold
        if best_match and best_score >= similarity_threshold:
            matches[track.id] = {
                "spotify_track": track,
                "musicbrainz_recording": best_match,
                "similarity_score": best_score,
            }

    return matches


def compare_artist_data(
    spotify_client: SpotifyClient,
    mb_client: MusicBrainzClient,
    artist_name: str,
) -> dict[str, Any]:
    """Compare artist data between Spotify and MusicBrainz.

    Args:
        spotify_client: Spotify client
        mb_client: MusicBrainz client
        artist_name: Artist name to search for

    Returns:
        Dictionary with comparison results
    """
    # Search for artist on both platforms
    spotify_artists = spotify_client.search_artists(artist_name)
    mb_artists = mb_client.search_artists(artist_name)

    if not spotify_artists or not mb_artists.artists:
        return {"error": "Artist not found on one or both platforms"}

    # Get the first artist from each platform
    spotify_artist = spotify_artists[0]
    mb_artist = mb_artists.artists[0]

    # Get artist details from both platforms
    spotify_stats = spotify_client.get_artist_stats(spotify_artist.id)
    album_counts_dict = spotify_stats.album_counts if hasattr(spotify_stats, "album_counts") else spotify_stats.get("album_counts", {})
    mb_stats = mb_client.get_artist_info(mb_artist.id)

    # Get album counts
    spotify_album_counts = {
        "album": 0,
        "single": 0,
        "compilation": 0,
        "total": 0,
    }

    for album_type, count in album_counts_dict.items():
        if album_type in spotify_album_counts:
            spotify_album_counts[album_type] = count

    mb_album_counts = mb_stats["release_group_counts"]

    # Compare top albums/release groups
    spotify_albums = spotify_client.get_all_artist_albums(
        artist_id=spotify_artist.id,
        album_types=["album"],
    )

    mb_release_groups = [
        rg
        for rg in mb_stats["all_release_groups"]
        if rg.primary_type and rg.primary_type.lower() == "album"
    ]

    # Match albums between platforms
    album_matches = []

    for spotify_album in spotify_albums[:10]:  # Limit to top 10 for performance
        mb_match = find_musicbrainz_release_group(spotify_album, mb_client, mb_artist.id)

        if mb_match:
            album_matches.append(
                {
                    "spotify_album": spotify_album,
                    "musicbrainz_release_group": mb_match,
                    "similarity_score": name_similarity(spotify_album.name, mb_match.title),
                },
            )

    # Compare top tracks
    spotify_top_tracks = spotify_client.get_artist_top_tracks(spotify_artist.id)
    track_matches = find_track_matches(spotify_top_tracks, mb_client, mb_artist.id)

    # Compile comparison results
    return {
        "spotify_artist": spotify_artist,
        "musicbrainz_artist": mb_artist,
        "spotify_album_counts": spotify_album_counts,
        "musicbrainz_album_counts": mb_album_counts,
        "album_matches": album_matches,
        "track_matches": track_matches,
    }
