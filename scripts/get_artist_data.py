#!/usr/bin/env python
"""Script for collecting hip-hop artist data and storing in MongoDB."""

import argparse
import os
import sys
import time
from typing import Any

from dotenv import load_dotenv
from pymongo import MongoClient
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from flow_metrics.clients.factory import create_musicbrainz_client, create_spotify_client
from flow_metrics.clients.musicbrainz import MusicBrainzClient, MusicBrainzError
from flow_metrics.clients.spotify import SpotifyClient, SpotifyError
from flow_metrics.config.settings import get_settings
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
        type=str,
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
    return parser


def connect_to_mongodb(uri: str, db_name: str) -> Any:
    """Connect to MongoDB.

    Args:
        uri: MongoDB connection URI
        db_name: Database name

    Returns:
        MongoDB database object
    """
    client = MongoClient(uri)
    return client[db_name]


def search_hip_hop_artists(
    spotify_client: SpotifyClient,
    limit: int = 50,
) -> list[SpotifyArtist]:
    """Search for hip-hop artists using Spotify search.

    Args:
        spotify_client: Spotify client
        limit: Maximum number of artists to return

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
    ]

    artists = []
    artists_seen = set()

    for term in search_terms:
        if len(artists) >= limit:
            break

        # Search for artists with the genre term
        try:
            results = spotify_client.search_artists(
                f"genre:{term}",
                limit=min(50, limit - len(artists)),
            )

            for artist in results:
                # Check if we already have this artist
                if artist.id not in artists_seen and (
                    # Check if artist has hip-hop related genres
                    any(genre in artist.genres for genre in ["hip hop", "rap", "trap", "drill"])
                ):
                    artists.append(artist)
                    artists_seen.add(artist.id)

                    if len(artists) >= limit:
                        break
        except SpotifyError as e:
            print(f"Error searching for term '{term}': {e}")

        # Add a small delay to avoid rate limiting
        time.sleep(1)

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
        "spotify_followers": getattr(artist.followers, "total", 0),
        "spotify_images": [img.url for img in artist.images] if artist.images else [],
        "albums": [],
        "singles": [],
        "compilations": [],
        "appears_on": [],
        "top_tracks": [],
        "musicbrainz_info": None,
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
                    "id": track.album.id,
                    "name": track.album.name,
                    "release_date": track.album.release_date,
                }
                if track.album
                else None,
            }
            for track in stats.top_tracks
        ]
    except SpotifyError as e:
        console.print(f"[yellow]Warning:[/yellow] Could not get Spotify stats: {e}")

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
                "image": album.images[0].url if album.images else None,
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
                "image": single.images[0].url if single.images else None,
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
                "image": compilation.images[0].url if compilation.images else None,
            }
            for compilation in compilations
        ]

        # Get appearances
        appearances = spotify_client.get_all_artist_albums(
            artist_id=artist.id,
            album_types=["appears_on"],
        )

        artist_data["appears_on"] = [
            {
                "id": appearance.id,
                "name": appearance.name,
                "release_date": appearance.release_date,
                "total_tracks": appearance.total_tracks,
                "album_type": appearance.album_type,
                "image": appearance.images[0].url if appearance.images else None,
            }
            for appearance in appearances
        ]
    except SpotifyError as e:
        console.print(f"[yellow]Warning:[/yellow] Could not get Spotify albums: {e}")

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
                    "release_counts": mb_info.get("release_group_counts", {}),
                }
    except MusicBrainzError as e:
        console.print(f"[yellow]Warning:[/yellow] Could not get MusicBrainz data: {e}")

    return artist_data


def store_artist_data(
    db: Any,
    collection_name: str,
    artist_data: dict[str, Any],
) -> None:
    """Store artist data in MongoDB.

    Args:
        db: MongoDB database
        collection_name: Collection name
        artist_data: Artist data to store
    """
    collection = db[collection_name]

    # Check if artist already exists
    existing = collection.find_one({"spotify_id": artist_data["spotify_id"]})

    if existing:
        # Update existing document
        collection.update_one(
            {"spotify_id": artist_data["spotify_id"]},
            {"$set": artist_data},
        )
    else:
        # Insert new document
        collection.insert_one(artist_data)


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

        # Get MongoDB URI from args or environment
        mongo_uri = args.mongo_uri or os.getenv("MONGODB_URI")

        if not mongo_uri:
            console.print(
                "[bold red]Error:[/bold red] MongoDB URI not provided. Use --mongo-uri or set MONGODB_URI environment variable.",
            )
            return

        # Connect to MongoDB
        console.print("Connecting to MongoDB...")
        db = connect_to_mongodb(mongo_uri, args.db_name)

        # Create clients
        console.print("Initializing API clients...")
        spotify_client = create_spotify_client()
        mb_client = create_musicbrainz_client()

        # Search for hip-hop artists
        console.print(f"Searching for up to {args.limit} hip-hop artists...")
        artists = search_hip_hop_artists(spotify_client, args.limit)

        console.print(f"Found {len(artists)} hip-hop artists.")

        # Process each artist
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Processing artists...", total=len(artists))

            for i, artist in enumerate(artists):
                progress.update(
                    task,
                    description=f"Processing {artist.name} ({i + 1}/{len(artists)})",
                )

                # Get comprehensive artist data
                artist_data = get_artist_full_data(spotify_client, mb_client, artist, console)

                # Store in MongoDB
                store_artist_data(db, args.collection, artist_data)

                # Update progress
                progress.advance(task)

                # Respect rate limits
                time.sleep(1)

        console.print(f"[bold green]Successfully processed {len(artists)} artists![/bold green]")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
