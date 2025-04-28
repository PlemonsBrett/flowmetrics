#!/usr/bin/env python
"""Example script demonstrating combined Spotify and MusicBrainz analysis."""

import argparse
import os
import sys
from typing import Any

from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from flow_metrics.clients.factory import create_musicbrainz_client, create_spotify_client
from flow_metrics.clients.musicbrainz import MusicBrainzError
from flow_metrics.clients.spotify import SpotifyError
from flow_metrics.utils.matching import compare_artist_data


def setup_argparse() -> argparse.ArgumentParser:
    """Set up command line argument parsing.

    Returns:
        Configured argument parser
    """
    parser = argparse.ArgumentParser(
        description="Compare artist data across Spotify and MusicBrainz",
    )
    parser.add_argument("artist", help="Artist name to search for")
    return parser


def display_artist_comparison(comparison_data: dict[str, Any], console: Console) -> None:
    """Display artist comparison data.

    Args:
        comparison_data: Comparison results
        console: Rich console
    """
    # Display artist info from both platforms
    spotify_artist = comparison_data["spotify_artist"]
    mb_artist = comparison_data["musicbrainz_artist"]

    console.print(f"[bold]Artist:[/bold] {spotify_artist.name}")
    console.print()

    # Create a comparison table for basic info
    info_table = Table(title="Basic Information")
    info_table.add_column("Metric")
    info_table.add_column("Spotify")
    info_table.add_column("MusicBrainz")

    # Add rows for basic info
    info_table.add_row(
        "ID",
        spotify_artist.id,
        mb_artist.id,
    )

    info_table.add_row(
        "Popularity",
        str(spotify_artist.popularity or "N/A"),
        "N/A",  # MusicBrainz doesn't have direct popularity equivalent
    )

    info_table.add_row(
        "Followers",
        f"{spotify_artist.followers.total:,}" if spotify_artist.followers else "N/A",
        "N/A",  # MusicBrainz doesn't track followers
    )

    genres_spotify = ", ".join(spotify_artist.genres or [])
    genres_mb = "N/A"  # Would need to extract from tags

    info_table.add_row(
        "Genres",
        genres_spotify or "N/A",
        genres_mb,
    )

    console.print(info_table)
    console.print()

    # Create a table for album counts
    album_table = Table(title="Release Counts")
    album_table.add_column("Type")
    album_table.add_column("Spotify")
    album_table.add_column("MusicBrainz")

    # Add rows for album counts
    spotify_counts = comparison_data["spotify_album_counts"]
    mb_counts = comparison_data["musicbrainz_album_counts"]

    album_table.add_row(
        "Albums",
        str(spotify_counts.get("album", 0)),
        str(mb_counts.get("album", 0)),
    )

    album_table.add_row(
        "Singles",
        str(spotify_counts.get("single", 0)),
        str(mb_counts.get("single", 0)),
    )

    album_table.add_row(
        "EPs",
        "N/A",  # Spotify doesn't separate EPs
        str(mb_counts.get("ep", 0)),
    )

    album_table.add_row(
        "Compilations",
        str(spotify_counts.get("compilation", 0)),
        str(mb_counts.get("compilation", 0)),
    )

    album_table.add_row(
        "Total",
        str(spotify_counts.get("total", 0)),
        str(mb_counts.get("total", 0)),
        style="bold",
    )

    console.print(album_table)
    console.print()

    # Display matched albums
    if comparison_data["album_matches"]:
        album_match_table = Table(title="Album Matches")
        album_match_table.add_column("Spotify Album")
        album_match_table.add_column("MusicBrainz Release Group")
        album_match_table.add_column("Similarity")

        for match in comparison_data["album_matches"]:
            spotify_album = match["spotify_album"]
            mb_release_group = match["musicbrainz_release_group"]
            similarity = match["similarity_score"]

            album_match_table.add_row(
                spotify_album.name,
                mb_release_group.title,
                f"{similarity:.2f}",
            )

        console.print(album_match_table)
        console.print()

    # Display matched tracks
    if comparison_data["track_matches"]:
        track_match_table = Table(title="Track Matches")
        track_match_table.add_column("Spotify Track")
        track_match_table.add_column("MusicBrainz Recording")
        track_match_table.add_column("Similarity")

        for match_data in comparison_data["track_matches"].values():
            spotify_track = match_data["spotify_track"]
            mb_recording = match_data["musicbrainz_recording"]
            similarity = match_data["similarity_score"]

            track_match_table.add_row(
                spotify_track.name,
                mb_recording.title,
                f"{similarity:.2f}",
            )

        console.print(track_match_table)
        console.print()


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

        # Create clients
        spotify_client = create_spotify_client()
        mb_client = create_musicbrainz_client()

        # Search for artist
        console.print(f"[bold]Comparing data for artist:[/bold] {args.artist}")
        console.print("[i]This may take a moment due to rate limiting...[/i]")
        console.print()

        # Compare artist data
        comparison_data = compare_artist_data(
            spotify_client=spotify_client,
            mb_client=mb_client,
            artist_name=args.artist,
        )

        if "error" in comparison_data:
            console.print(f"[bold red]Error:[/bold red] {comparison_data['error']}")
            return

        # Display comparison results
        display_artist_comparison(comparison_data, console)

    except (SpotifyError, MusicBrainzError) as e:
        console.print(f"[bold red]API Error:[/bold red] {e}")
    except KeyboardInterrupt:
        console.print("\n[bold]Operation cancelled.[/bold]")
    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/bold red] {e}")


if __name__ == "__main__":
    main()
