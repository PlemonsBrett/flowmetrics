#!/usr/bin/env python
"""Script for collecting hip-hop artist data and storing in MongoDB."""

import argparse
import os
import sys
import time
from typing import Any

from dotenv import load_dotenv
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

# Add the project root to the path if running as script
if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
    __package__ = "flow_metrics.scripts"

from flow_metrics.clients.factory import create_musicbrainz_client, create_spotify_client
from flow_metrics.clients.musicbrainz import MusicBrainzClient, MusicBrainzError
from flow_metrics.clients.spotify import SpotifyClient, SpotifyError
from flow_metrics.config.settings import get_settings
from flow_metrics.db.mongodb import MongoDBClient
from flow_metrics.models.spotify import SpotifyArtist


def setup_argparse() -> argparse.ArgumentParser:
    """Set up command line argument parsing.

    Returns:
        Configured argument parser
    """
    settings = get_settings()

    parser = argparse.ArgumentParser(description="Collect hip-hop artist data for MongoDB")
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Limit number of artists to collect",
    )
    parser.add_argument(
        "--mongo-uri",
        default=settings.mongo_uri,
        help="MongoDB connection URI",
    )
    parser.add_argument(
        "--db-name",
        default=settings.mongo_db,
        help="MongoDB database name",
    )
    parser.add_argument(
        "--collection",
        default=settings.mongo_collection,
        help="MongoDB collection name",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip artists that already exist in the database",
    )
    return parser


def search_hip_hop_artists(
    spotify_client: SpotifyClient,
    limit: int = 50,
    console: Console = Console(),
) -> list[SpotifyArtist]:
    """Search for hip-hop artists using Spotify search.

    Args:
        spotify_client: Spotify client
        limit: Maximum number of artists to return
        console: Rich console for output

    Returns:
        List of hip-hop artists
    """
    # List of search terms to find hip-hop artists
    search_terms = [
        "hip hop",
        "rap",
        "trap",
        "drill",
        "conscious rap",
        "gangsta rap",
        "boom bap",
        "horrorcore",
    ]

    # List of notable hip-hop artists to ensure are included
    notable_artists = [
        "Kendrick Lamar",
        "Jay-Z",
        "Kanye West",
        "Drake",
        "Nas",
        "Tupac Shakur",
        "The Notorious B.I.G.",
        "Eminem",
        "Run-DMC",
        "Wu-Tang Clan",
        "A Tribe Called Quest",
    ]

    artists = []
    artists_seen = set()

    # First add notable artists
    for artist_name in notable_artists:
        if len(artists) >= limit:
            break

        try:
            results = spotify_client.search_artists(artist_name, limit=1)
            if results and results[0].id not in artists_seen:
                artists.append(results[0])
                artists_seen.add(results[0].id)
                console.print(f"Added notable artist: {results[0].name}")
        except SpotifyError as e:
            console.print(
                f"[yellow]Warning:[/yellow] Could not find notable artist '{artist_name}': {e}",
            )

        # Add a small delay to avoid rate limiting
        time.sleep(0.5)

    # Then search for additional artists by genre
    for term in search_terms:
        if len(artists) >= limit:
            break

        # Search for artists with the genre term
        try:
            console.print(f"Searching for artists with term: {term}")
            results = spotify_client.search_artists(
                f"genre:{term}",
                limit=min(20, limit - len(artists)),
            )

            for artist in results:
                # Check if we already have this artist
                if artist.id not in artists_seen and (
                    # Check if artist has hip-hop related genres
                    any(
                        genre in " ".join(artist.genres).lower()
                        for genre in ["hip hop", "rap", "trap", "drill"]
                    )
                ):
                    artists.append(artist)
                    artists_seen.add(artist.id)
                    console.print(f"Added artist from search: {artist.name}")

                    if len(artists) >= limit:
                        break
        except SpotifyError as e:
            console.print(f"[yellow]Warning:[/yellow] Error searching for term '{term}': {e}")

        # Add a small delay to avoid rate limiting
        time.sleep(1)

    console.print(f"[green]Found {len(artists)} hip-hop artists in total[/green]")
    return artists


def get_artist_full_data(
    spotify_client: SpotifyClient,
    mb_client: MusicBrainzClient,
    artist: SpotifyArtist,
    console: Console,
) -> dict[str, Any]:
    """Get comprehensive artist data from both Spotify and MusicBrainz.

    Args:
        spotify_client: Spotify client
        mb_client: MusicBrainz client
        artist: Spotify artist object
        console: Rich console for output

    Returns:
        Dictionary with comprehensive artist data
    """
    artist_data = {
        "spotify_id": artist.id,
        "name": artist.name,
        "genres": artist.genres,
        "spotify_popularity": artist.popularity,
        "spotify_followers": getattr(artist.followers, "total", 0) if artist.followers else 0,
        "spotify_images": [img.url for img in artist.images] if artist.images else [],
        "spotify_uri": artist.uri,
        "external_urls": artist.external_urls,
        "albums": [],
        "singles": [],
        "compilations": [],
        "appears_on": [],
        "top_tracks": [],
        "musicbrainz_info": None,
        "last_updated": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
    }

    # Get Spotify artist stats
    try:
        stats = spotify_client.get_artist_stats(artist_id=artist.id)

        # Add album counts
        artist_data["album_counts"] = stats.album_counts

        # Get top tracks
        artist_data["top_tracks"] = [
            {
                "id": track.id,
                "name": track.name,
                "popularity": track.popularity,
                "explicit": track.explicit,
                "duration_ms": track.duration_ms,
                "album": {
                    "id": track.album.id if track.album else None,
                    "name": track.album.name if track.album else None,
                    "release_date": track.album.release_date if track.album else None,
                }
                if track.album
                else None,
            }
            for track in stats.top_tracks
        ]
    except SpotifyError as e:
        console.print(
            f"[yellow]Warning:[/yellow] Could not get Spotify stats for {artist.name}: {e}",
        )

    # Get all artist albums
    try:
        # Get albums
        albums = spotify_client.get_all_artist_albums(
            artist_id=artist.id,
            album_types=["album"],
        )

        artist_data["albums"] = [
            {
                "id": album.id,
                "name": album.name,
                "release_date": album.release_date,
                "total_tracks": album.total_tracks,
                "album_type": album.album_type,
                "image": album.images[0].url if album.images and len(album.images) > 0 else None,
            }
            for album in albums
        ]

        # Get singles
        singles = spotify_client.get_all_artist_albums(
            artist_id=artist.id,
            album_types=["single"],
        )

        artist_data["singles"] = [
            {
                "id": single.id,
                "name": single.name,
                "release_date": single.release_date,
                "total_tracks": single.total_tracks,
                "album_type": single.album_type,
                "image": single.images[0].url if single.images and len(single.images) > 0 else None,
            }
            for single in singles
        ]

        # Get compilations
        compilations = spotify_client.get_all_artist_albums(
            artist_id=artist.id,
            album_types=["compilation"],
        )

        artist_data["compilations"] = [
            {
                "id": compilation.id,
                "name": compilation.name,
                "release_date": compilation.release_date,
                "total_tracks": compilation.total_tracks,
                "album_type": compilation.album_type,
                "image": compilation.images[0].url
                if compilation.images and len(compilation.images) > 0
                else None,
            }
            for compilation in compilations
        ]

        # Get appearances
        appearances = spotify_client.get_all_artist_albums(
            artist_id=artist.id,
            album_types=["appears_on"],
        )

        # Limit appearances to 100 to keep document size reasonable
        appearances = appearances[:100] if len(appearances) > 100 else appearances

        artist_data["appears_on"] = [
            {
                "id": appearance.id,
                "name": appearance.name,
                "release_date": appearance.release_date,
                "total_tracks": appearance.total_tracks,
                "album_type": appearance.album_type,
                "image": appearance.images[0].url
                if appearance.images and len(appearance.images) > 0
                else None,
            }
            for appearance in appearances
        ]
    except SpotifyError as e:
        console.print(
            f"[yellow]Warning:[/yellow] Could not get Spotify albums for {artist.name}: {e}",
        )

    # Try to find MusicBrainz data
    try:
        mb_results = mb_client.search_artists(artist.name)

        if mb_results.artists:
            # Find the best match
            best_match = None
            highest_score = 0

            for mb_artist in mb_results.artists:
                # Use the score provided by MusicBrainz
                score = getattr(mb_artist, "score", 0)
                if score > highest_score:
                    highest_score = score
                    best_match = mb_artist

            if best_match and highest_score > 70:  # Only use if confidence is high
                # Get MusicBrainz artist info
                mb_info = mb_client.get_artist_info(best_match.id)

                artist_data["musicbrainz_info"] = {
                    "id": best_match.id,
                    "name": best_match.name,
                    "disambiguation": best_match.disambiguation,
                    "country": best_match.country,
                    "type": best_match.type,
                    "life_span": {
                        "begin": best_match.life_span.begin if best_match.life_span else None,
                        "end": best_match.life_span.end if best_match.life_span else None,
                        "ended": best_match.life_span.ended if best_match.life_span else None,
                    },
                    "release_counts": mb_info["release_group_counts"]
                    if "release_group_counts" in mb_info
                    else {},
                }
    except MusicBrainzError as e:
        console.print(
            f"[yellow]Warning:[/yellow] Could not get MusicBrainz data for {artist.name}: {e}",
        )

    return artist_data


def main() -> None:
    """Main function."""
    # Load environment variables
    load_dotenv()

    # Set up console
    console = Console()

    try:
        # Parse command line arguments
        parser = setup_argparse()
        args = parser.parse_args()

        # Connect to MongoDB
        console.print("Connecting to MongoDB...")
        mongo_client = MongoDBClient(args.mongo_uri, args.db_name, args.collection)

        # Create API clients
        console.print("Initializing API clients...")
        spotify_client = create_spotify_client()
        mb_client = create_musicbrainz_client()

        # Add helper function to convert Pydantic models to dictionaries
        def convert_model_to_dict(obj):
            """Convert Pydantic models to dictionaries for MongoDB storage."""
            if hasattr(obj, "model_dump"):
                # For newer Pydantic v2.x
                return obj.model_dump()
            if hasattr(obj, "dict") and callable(obj.dict):
                # For older Pydantic v1.x
                return obj.dict()
            if isinstance(obj, dict):
                return {k: convert_model_to_dict(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [convert_model_to_dict(item) for item in obj]
            return obj

        # Get current count of artists in database
        existing_count = mongo_client.count_artists()
        console.print(f"Found {existing_count} artists already in the database")

        # Fetch more artists than we need so we have extras if some already exist
        search_limit = min(args.limit * 3, 150)  # Get up to 3x what we need, max 150
        console.print(f"Searching for up to {search_limit} hip-hop artists...")
        all_artists = search_hip_hop_artists(spotify_client, search_limit, console)

        console.print(f"[bold]Found {len(all_artists)} total hip-hop artists from search.[/bold]")

        # Filter for artists not already in the database
        new_artists = []
        for artist in all_artists:
            # Check if artist exists in database
            if not mongo_client.find_artist_by_spotify_id(artist.id):
                new_artists.append(artist)

            # Stop once we've found enough new artists
            if len(new_artists) >= args.limit:
                break

        console.print(f"[bold]Found {len(new_artists)} new artists to add to the database.[/bold]")

        # If we didn't find any new artists, stop here
        if not new_artists:
            console.print(
                "[bold yellow]No new artists found to add to the database. Exiting.[/bold yellow]"
            )
            return

        # Process each new artist
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Processing artists...", total=len(new_artists))

            for i, artist in enumerate(new_artists):
                progress.update(
                    task,
                    description=f"Processing {artist.name} ({i + 1}/{len(new_artists)})",
                )

                # Get comprehensive artist data
                artist_data = get_artist_full_data(spotify_client, mb_client, artist, console)

                # Convert to MongoDB-compatible format
                artist_data = convert_model_to_dict(artist_data)

                # Store in MongoDB
                result = mongo_client.upsert_artist(artist_data)

                progress.console.print(f"Inserted new artist: {artist.name}")

                # Update progress
                progress.advance(task)

                # Respect rate limits
                time.sleep(1)

        # Print summary
        total_count = mongo_client.count_artists()
        console.print(
            f"[bold green]Successfully processed {len(new_artists)} new artists![/bold green]"
        )
        console.print(f"Total artists in database: {total_count}")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        import traceback

        traceback.print_exc()
