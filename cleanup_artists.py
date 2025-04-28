#!/usr/bin/env python
"""Script for cleaning up artist data in MongoDB."""

import argparse
import os
import sys
import time
from typing import Any

from dotenv import load_dotenv
from pymongo import MongoClient
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

# Add the project root to the path if running as script
if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
    __package__ = "flow_metrics.scripts"


def setup_argparse() -> argparse.ArgumentParser:
    """Set up command line argument parsing.

    Returns:
        Configured argument parser
    """
    parser = argparse.ArgumentParser(description="Clean up artist data in MongoDB")
    parser.add_argument(
        "--mongo-uri",
        required=True,
        help="MongoDB connection URI",
    )
    parser.add_argument(
        "--db-name",
        required=True,
        help="MongoDB database name",
    )
    parser.add_argument(
        "--collection",
        required=True,
        help="MongoDB collection name",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't actually update the database, just show what would be done",
    )
    return parser


def cleanup_artist(artist_data: dict[str, Any]) -> dict[str, Any]:
    """Clean up artist data structure.

    Args:
        artist_data: The artist data to clean up

    Returns:
        Cleaned up artist data
    """
    # Create a new document to hold the cleaned data
    cleaned_data = {
        "_id": artist_data["_id"],
        "spotify_id": artist_data["spotify_id"],
        "name": artist_data["name"],
        "genres": artist_data["genres"],
        "spotify_popularity": artist_data.get("spotify_popularity", 0),
        "spotify_followers": artist_data.get("spotify_followers", 0),
        "spotify_uri": artist_data.get("spotify_uri", ""),
        "external_urls": artist_data.get("external_urls", {}),
    }

    # Extract MusicBrainz data
    if "musicbrainz_info" in artist_data and artist_data["musicbrainz_info"]:
        mb_info = artist_data["musicbrainz_info"]
        cleaned_data["mbid"] = mb_info.get("id")
        cleaned_data["disambiguation"] = mb_info.get("disambiguation")
        cleaned_data["country"] = mb_info.get("country")
        cleaned_data["type"] = mb_info.get("type")

        # Extract life span information
        if "life_span" in mb_info and mb_info["life_span"]:
            cleaned_data["life_span"] = mb_info["life_span"]

        # Use MusicBrainz release counts as the primary album counts
        if "release_counts" in mb_info and mb_info["release_counts"]:
            cleaned_data["release_counts"] = mb_info["release_counts"]

    # If MusicBrainz release counts are not available, use Spotify album counts
    if "release_counts" not in cleaned_data and "album_counts" in artist_data:
        cleaned_data["release_counts"] = artist_data["album_counts"]

    # Select the most recent/highest quality album/single/compilation objects
    if "albums" in artist_data and artist_data["albums"]:
        # Sort albums by release date (newest first)
        albums = sorted(
            artist_data["albums"],
            key=lambda x: x.get("release_date", ""),
            reverse=True,
        )
        cleaned_data["albums"] = albums

    if "singles" in artist_data and artist_data["singles"]:
        # Sort singles by release date (newest first)
        singles = sorted(
            artist_data["singles"],
            key=lambda x: x.get("release_date", ""),
            reverse=True,
        )
        cleaned_data["singles"] = singles

    if "compilations" in artist_data and artist_data["compilations"]:
        cleaned_data["compilations"] = artist_data["compilations"]

    # Store top tracks
    if "top_tracks" in artist_data and artist_data["top_tracks"]:
        cleaned_data["top_tracks"] = artist_data["top_tracks"]

    # Get a single image URL (highest quality)
    if "spotify_images" in artist_data and artist_data["spotify_images"]:
        # Just use the first image (typically the highest quality)
        cleaned_data["image_uri"] = artist_data["spotify_images"][0]

    # Preserve the last updated timestamp
    if "last_updated" in artist_data:
        cleaned_data["last_updated"] = artist_data["last_updated"]
    else:
        cleaned_data["last_updated"] = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())

    return cleaned_data


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
        client = MongoClient(args.mongo_uri)
        db = client[args.db_name]
        collection = db[args.collection]

        # Get all artists from the collection
        console.print("Retrieving artists from database...")
        artists = list(collection.find({}))
        console.print(f"Found {len(artists)} artists in the database.")

        # Process each artist
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Processing artists...", total=len(artists))

            for artist in artists:
                progress.update(
                    task,
                    description=f"Processing {artist['name']} ({progress.tasks[0].completed + 1}/{len(artists)})",
                )

                # Clean up the artist data
                cleaned_artist = cleanup_artist(artist)

                # Update the database (if not a dry run)
                if not args.dry_run:
                    result = collection.replace_one({"_id": artist["_id"]}, cleaned_artist)
                    if result.modified_count > 0:
                        progress.console.print(f"Updated artist: {artist['name']}")
                    else:
                        progress.console.print(f"No changes needed for artist: {artist['name']}")
                else:
                    # In dry run mode, just print what would be done
                    progress.console.print(f"Would update artist: {artist['name']}")

                # Update progress
                progress.advance(task)

        console.print("[bold green]Successfully processed all artists![/bold green]")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
