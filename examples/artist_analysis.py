#!/usr/bin/env python
"""Example script demonstrating the Spotify client for artist analysis."""

import argparse
import os
import sys

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from flow_metrics.clients.factory import create_spotify_client
from flow_metrics.clients.spotify import SpotifyClient, SpotifyError
from flow_metrics.models.spotify import SpotifyArtist


def setup_argparse() -> argparse.ArgumentParser:
    """Set up command line argument parsing.

    Returns:
        Configured argument parser
    """
    parser = argparse.ArgumentParser(description="Analyze Spotify artist data")
    parser.add_argument("artist", help="Artist name to search for")
    parser.add_argument(
        "--market",
        default="US",
        help="Market to use for Spotify API (ISO 3166-1 alpha-2 country code)",
    )
    parser.add_argument(
        "--album-type",
        choices=["album", "single", "compilation", "appears_on"],
        nargs="+",
        help="Album types to include in analysis",
    )
    parser.add_argument(
        "--timeline",
        action="store_true",
        help="Show artist release timeline",
    )
    parser.add_argument(
        "--top-tracks",
        action="store_true",
        help="Show artist top tracks",
    )
    return parser


def display_artist_info(artist: SpotifyArtist, console: Console) -> None:
    """Display basic artist information.

    Args:
        artist: Artist object
        console: Rich console
    """
    # Create a panel with artist info
    artist_panel = Panel(
        f"[bold]{artist.name}[/bold]\n\n"
        f"Popularity: {artist.popularity}/100\n"
        f"Followers: {getattr(artist.followers, 'total', 'Unknown'):,}\n"
        f"Genres: {', '.join(artist.genres)}\n"
        f"Spotify URL: {getattr(artist.external_urls, 'spotify', '')}",
    )

    console.print(artist_panel)


def display_artist_stats(
    client: SpotifyClient, artist_id: str, market: str, console: Console,
) -> None:
    """Display comprehensive artist statistics.

    Args:
        client: Spotify client
        artist_id: Artist ID
        market: Market code
        console: Rich console
    """
    # Get artist statistics
    stats = client.get_artist_stats(artist_id=artist_id, market=market)

    # Create a table for album counts
    album_table = Table(title="Discography")
    album_table.add_column("Type")
    album_table.add_column("Count")

    for album_type, count in stats.album_counts.items():
        if album_type != "total":
            album_table.add_row(album_type.capitalize(), str(count))

    album_table.add_row("Total", str(stats.album_counts["total"]), style="bold")

    console.print(album_table)
    console.print()


def display_top_tracks(
    client: SpotifyClient, artist_id: str, market: str, console: Console,
) -> None:
    """Display artist top tracks.

    Args:
        client: Spotify client
        artist_id: Artist ID
        market: Market code
        console: Rich console
    """
    # Get top tracks
    top_tracks = client.get_artist_top_tracks(artist_id=artist_id, market=market)

    # Create a table for top tracks
    tracks_table = Table(title="Top Tracks")
    tracks_table.add_column("#")
    tracks_table.add_column("Track")
    tracks_table.add_column("Popularity")
    tracks_table.add_column("Duration")
    tracks_table.add_column("Explicit")

    for i, track in enumerate(top_tracks, 1):
        # Format duration as mm:ss
        minutes = track.duration_ms // 60000
        seconds = (track.duration_ms % 60000) // 1000
        duration = f"{minutes}:{seconds:02d}"

        # Format explicit flag
        explicit = "Yes" if track.explicit else "No"

        tracks_table.add_row(
            str(i),
            track.name,
            f"{track.popularity or 0}/100",
            duration,
            explicit,
        )

    console.print(tracks_table)
    console.print()


def display_timeline(
    client: SpotifyClient,
    artist_id: str,
    album_types: list[str] | None,
    market: str,
    console: Console,
) -> None:
    """Display artist release timeline.

    Args:
        client: Spotify client
        artist_id: Artist ID
        album_types: Album types to include
        market: Market code
        console: Rich console
    """
    # Get artist release timeline
    timeline_data = client.get_artist_timeline(
        artist_id=artist_id,
        album_types=album_types,
        market=market,
    )

    # Create timeline table
    timeline_table = Table(title="Release Timeline")
    timeline_table.add_column("Year")
    timeline_table.add_column("Release")
    timeline_table.add_column("Type")
    timeline_table.add_column("Tracks")

    # Add timeline data
    for year, albums in timeline_data.timeline.items():
        for i, album in enumerate(albums):
            # Only show year in first row for this year
            year_display = year if i == 0 else ""

            timeline_table.add_row(
                year_display,
                album.name,
                album.album_type.capitalize(),
                str(album.total_tracks),
            )

    console.print(timeline_table)
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

        # Create Spotify client
        client = create_spotify_client()

        # Search for artist
        console.print(f"[bold]Searching for artist:[/bold] {args.artist}")
        artists = client.search_artists(args.artist)

        if not artists:
            console.print("[bold red]No artists found.[/bold red]")
            return

        # Display artist selection if multiple artists found
        if len(artists) > 1:
            console.print("[bold]Multiple artists found. Please select one:[/bold]")
            for i, artist in enumerate(artists, 1):
                console.print(f"{i}. {artist.name}")

            # Get user selection
            selection = 0
            while selection < 1 or selection > len(artists):
                try:
                    selection = int(input("Enter selection number: "))
                except ValueError:
                    console.print("[bold red]Invalid input. Please enter a number.[/bold red]")

            artist = artists[selection - 1]
        else:
            # Use the first artist if only one found
            artist = artists[0]

        # Display artist info
        console.print()
        display_artist_info(artist, console)
        console.print()

        # Display artist stats
        display_artist_stats(client, artist.id, args.market, console)

        # Display top tracks if requested
        if args.top_tracks:
            display_top_tracks(client, artist.id, args.market, console)

        # Display timeline if requested
        if args.timeline:
            display_timeline(client, artist.id, args.album_type, args.market, console)

    except SpotifyError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
    except KeyboardInterrupt:
        console.print("\n[bold]Operation cancelled.[/bold]")
    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/bold red] {e}")


if __name__ == "__main__":
    main()
