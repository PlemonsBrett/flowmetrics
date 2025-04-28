#!/usr/bin/env python
"""Script for viewing artist data from MongoDB."""

import argparse
import os
import sys
from typing import Any

from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

# Add the project root to the path if running as script
if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
    __package__ = "flow_metrics.scripts"

from flow_metrics.config.settings import get_settings
from flow_metrics.db.mongodb import MongoDBClient


def setup_argparse() -> argparse.ArgumentParser:
    """Set up command line argument parsing.

    Returns:
        Configured argument parser
    """
    settings = get_settings()

    parser = argparse.ArgumentParser(description="View artist data from MongoDB")
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
        "--name",
        help="Filter by artist name (case-insensitive)",
    )
    parser.add_argument(
        "--genre",
        help="Filter by genre (case-insensitive)",
    )
    parser.add_argument(
        "--count",
        action="store_true",
        help="Only show count of matching artists",
    )
    parser.add_argument(
        "--details",
        action="store_true",
        help="Show detailed information about each artist",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Limit number of artists to display",
    )
    return parser


def display_artist_summary(artist: dict[str, Any], console: Console) -> None:
    """Display a summary of artist information.

    Args:
        artist: Artist data
        console: Rich console for output
    """
    table = Table(title=f"Artist: {artist['name']}")

    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Spotify ID", artist["spotify_id"])
    table.add_row("Genres", ", ".join(artist["genres"]) if artist["genres"] else "None")
    table.add_row("Popularity", str(artist["spotify_popularity"]))
    table.add_row("Followers", f"{artist['spotify_followers']:,}")

    # Album counts
    if "album_counts" in artist:
        album_counts = artist["album_counts"]
        table.add_row(
            "Albums",
            f"Albums: {album_counts.get('album', 0)}, "
            f"Singles: {album_counts.get('single', 0)}, "
            f"Compilations: {album_counts.get('compilation', 0)}, "
            f"Total: {album_counts.get('total', 0)}",
        )

    # MusicBrainz info
    if artist.get("musicbrainz_info"):
        mb_info = artist["musicbrainz_info"]
        table.add_row("MusicBrainz ID", mb_info["id"])

        if mb_info.get("country"):
            table.add_row("Country", mb_info["country"])

        if mb_info.get("life_span") and mb_info["life_span"].get("begin"):
            begin = mb_info["life_span"]["begin"]
            end = mb_info["life_span"]["end"] or "present"
            table.add_row("Active Period", f"{begin} - {end}")

    # Top tracks
    if artist.get("top_tracks"):
        top_track_names = [track["name"] for track in artist["top_tracks"][:5]]
        table.add_row("Top Tracks", ", ".join(top_track_names))

    console.print(table)


def display_artist_details(artist: dict[str, Any], console: Console) -> None:
    """Display detailed artist information.

    Args:
        artist: Artist data
        console: Rich console for output
    """
    # Basic info table
    basic_table = Table(title=f"Artist: {artist['name']}")

    basic_table.add_column("Property", style="cyan")
    basic_table.add_column("Value", style="green")

    basic_table.add_row("Spotify ID", artist["spotify_id"])
    basic_table.add_row("Genres", ", ".join(artist["genres"]) if artist["genres"] else "None")
    basic_table.add_row("Popularity", str(artist["spotify_popularity"]))
    basic_table.add_row("Followers", f"{artist['spotify_followers']:,}")

    if "spotify_uri" in artist:
        basic_table.add_row("Spotify URI", artist["spotify_uri"])

    if "external_urls" in artist and "spotify" in artist["external_urls"]:
        basic_table.add_row("Spotify URL", artist["external_urls"]["spotify"])

    # MusicBrainz info
    if artist.get("musicbrainz_info"):
        mb_info = artist["musicbrainz_info"]
        basic_table.add_row("MusicBrainz ID", mb_info["id"])

        if mb_info.get("country"):
            basic_table.add_row("Country", mb_info["country"])

        if mb_info.get("disambiguation"):
            basic_table.add_row("Disambiguation", mb_info["disambiguation"])

        if mb_info.get("type"):
            basic_table.add_row("Type", mb_info["type"])

        if mb_info.get("life_span") and mb_info["life_span"].get("begin"):
            begin = mb_info["life_span"]["begin"]
            end = mb_info["life_span"]["end"] or "present"
            basic_table.add_row("Active Period", f"{begin} - {end}")

    if "last_updated" in artist:
        basic_table.add_row("Last Updated", artist["last_updated"])

    console.print(basic_table)

    # Albums table
    if artist.get("albums"):
        albums_table = Table(title="Albums")

        albums_table.add_column("Name", style="green")
        albums_table.add_column("Release Date", style="cyan")
        albums_table.add_column("Tracks", style="magenta")

        for album in artist["albums"]:
            albums_table.add_row(
                album["name"],
                album["release_date"],
                str(album["total_tracks"]),
            )

        console.print(albums_table)

    # Singles table
    if artist.get("singles") and len(artist["singles"]) > 0:
        singles_table = Table(title="Singles")

        singles_table.add_column("Name", style="green")
        singles_table.add_column("Release Date", style="cyan")
        singles_table.add_column("Tracks", style="magenta")

        for single in artist["singles"]:
            singles_table.add_row(
                single["name"],
                single["release_date"],
                str(single["total_tracks"]),
            )

        console.print(singles_table)

    # Top tracks table
    if artist.get("top_tracks"):
        top_tracks_table = Table(title="Top Tracks")

        top_tracks_table.add_column("#", style="cyan")
        top_tracks_table.add_column("Track", style="green")
        top_tracks_table.add_column("Popularity", style="magenta")
        top_tracks_table.add_column("Album", style="yellow")

        for i, track in enumerate(artist["top_tracks"], 1):
            album_name = track.get("album", {}).get("name", "N/A") if track.get("album") else "N/A"

            top_tracks_table.add_row(
                str(i),
                track["name"],
                str(track.get("popularity", "N/A")),
                album_name,
            )

        console.print(top_tracks_table)


def find_artists(
    mongo_client: MongoDBClient,
    name: str | None = None,
    genre: str | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """Find artists in the database.

    Args:
        mongo_client: MongoDB client
        name: Filter by artist name (case-insensitive)
        genre: Filter by genre (case-insensitive)
        limit: Maximum number of artists to return

    Returns:
        List of matching artists
    """
    db_collection = mongo_client.get_collection()

    # Build query
    query = {}

    if name:
        query["name"] = {"$regex": name, "$options": "i"}

    if genre:
        query["genres"] = {"$regex": genre, "$options": "i"}

    # Execute query
    results = db_collection.find(query).limit(limit)

    return list(results)


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

        # Find artists
        artists = find_artists(
            mongo_client,
            args.name,
            args.genre,
            args.limit,
        )

        # Display results
        if args.count:
            console.print(f"[bold]Found {len(artists)} matching artists[/bold]")
        else:
            console.print(f"[bold]Found {len(artists)} matching artists:[/bold]")

            for artist in artists:
                if args.details:
                    display_artist_details(artist, console)
                    console.print("\n")
                else:
                    display_artist_summary(artist, console)

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
