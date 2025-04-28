#!/usr/bin/env python
"""Example script demonstrating the MusicBrainz client for artist analysis."""

import argparse
import os
import sys

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from flow_metrics.clients.factory import create_musicbrainz_client
from flow_metrics.clients.musicbrainz import MusicBrainzClient, MusicBrainzError
from flow_metrics.models.musicbrainz import MusicBrainzArtist, MusicBrainzReleaseGroup


def setup_argparse() -> argparse.ArgumentParser:
    """Set up command line argument parsing.

    Returns:
        Configured argument parser
    """
    parser = argparse.ArgumentParser(description="Analyze MusicBrainz artist data")
    parser.add_argument("artist", help="Artist name to search for")
    parser.add_argument(
        "--release-type",
        choices=["album", "single", "ep", "compilation", "soundtrack", "live"],
        nargs="+",
        help="Release types to include in analysis",
    )
    parser.add_argument(
        "--timeline",
        action="store_true",
        help="Show artist release timeline",
    )
    parser.add_argument(
        "--similar",
        action="store_true",
        help="Show similar artists",
    )
    return parser


def display_artist_info(artist: MusicBrainzArtist, console: Console) -> None:
    """Display basic artist information.

    Args:
        artist: Artist object
        console: Rich console
    """
    # Create a panel with artist info
    artist_info = [f"[bold]{artist.name}[/bold]"]

    if artist.disambiguation:
        artist_info.append(f"[i]{artist.disambiguation}[/i]")

    artist_info.append("")

    if artist.type:
        artist_info.append(f"Type: {artist.type}")

    if artist.gender:
        artist_info.append(f"Gender: {artist.gender}")

    if artist.country:
        artist_info.append(f"Country: {artist.country}")

    if artist.life_span:
        begin = artist.life_span.begin or "?"
        end = artist.life_span.end or "present" if artist.life_span.ended else "present"
        artist_info.append(f"Active: {begin} - {end}")

    artist_panel = Panel("\n".join(artist_info))
    console.print(artist_panel)


def display_release_timeline(
    timeline: dict[str, list[MusicBrainzReleaseGroup]],
    console: Console,
) -> None:
    """Display artist release timeline.

    Args:
        timeline: Dictionary with years as keys and lists of release groups as values
        console: Rich console
    """
    # Create timeline table
    timeline_table = Table(title="Release Timeline")
    timeline_table.add_column("Year")
    timeline_table.add_column("Release")
    timeline_table.add_column("Type")

    # Add timeline data
    for year, release_groups in timeline.items():
        for i, release_group in enumerate(release_groups):
            # Only show year in first row for this year
            year_display = year if i == 0 else ""

            # Determine type
            release_type = release_group.primary_type or "Other"
            if release_group.secondary_types:
                release_type += f" ({', '.join(release_group.secondary_types)})"

            timeline_table.add_row(
                year_display,
                release_group.title,
                release_type,
            )

    console.print(timeline_table)
    console.print()


def display_similar_artists(client: MusicBrainzClient, artist_id: str, console: Console) -> None:
    """Display similar artists.

    Args:
        client: MusicBrainz client
        artist_id: Artist ID
        console: Rich console
    """
    # Get similar artists
    similar_artists = client.find_similar_artists(artist_id)

    if not similar_artists:
        console.print("[i]No similar artists found.[/i]")
        return

    # Create a table for similar artists
    similar_table = Table(title="Similar Artists")
    similar_table.add_column("Name")
    similar_table.add_column("Type")
    similar_table.add_column("Country")

    for artist in similar_artists:
        similar_table.add_row(
            artist.name,
            artist.type or "",
            artist.country or "",
        )

    console.print(similar_table)
    console.print()


def display_artist_stats(client: MusicBrainzClient, artist_id: str, console: Console) -> None:
    """Display comprehensive artist statistics.

    Args:
        client: MusicBrainz client
        artist_id: Artist ID
        console: Rich console
    """
    # Get artist stats
    stats = client.get_artist_info(artist_id)

    # Create a table for release counts
    release_table = Table(title="Discography")
    release_table.add_column("Type")
    release_table.add_column("Count")

    for release_type, count in stats["release_group_counts"].items():
        if release_type != "total":
            release_table.add_row(release_type.capitalize(), str(count))

    release_table.add_row("Total", str(stats["release_group_counts"]["total"]), style="bold")

    console.print(release_table)
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

        # Create MusicBrainz client
        client = create_musicbrainz_client()

        # Search for artist
        console.print(f"[bold]Searching for artist:[/bold] {args.artist}")
        result = client.search_artists(args.artist)

        if result.count == 0:
            console.print("[bold red]No artists found.[/bold red]")
            return

        # Display artist selection if multiple artists found
        if result.count > 1:
            console.print("[bold]Multiple artists found. Please select one:[/bold]")
            for i, artist in enumerate(result.artists, 1):
                artist_desc = artist.name
                if artist.disambiguation:
                    artist_desc += f" ({artist.disambiguation})"
                console.print(f"{i}. {artist_desc}")

            # Get user selection
            selection = 0
            while selection < 1 or selection > len(result.artists):
                try:
                    selection = int(input("Enter selection number: "))
                except ValueError:
                    console.print("[bold red]Invalid input. Please enter a number.[/bold red]")

            artist = result.artists[selection - 1]
        else:
            # Use the first artist if only one found
            artist = result.artists[0]

        # Display artist info
        console.print()
        display_artist_info(artist, console)
        console.print()

        # Display artist stats
        display_artist_stats(client, artist.id, console)

        # Display similar artists if requested
        if args.similar:
            display_similar_artists(client, artist.id, console)

        # Display timeline if requested
        if args.timeline:
            timeline = client.get_artist_timeline(artist.id, release_types=args.release_type)
            if timeline:
                display_release_timeline(timeline, console)
            else:
                console.print("[i]No releases found for timeline.[/i]")

    except MusicBrainzError as e:
        console.print(f"[bold red]MusicBrainz Error:[/bold red] {e}")
    except KeyboardInterrupt:
        console.print("\n[bold]Operation cancelled.[/bold]")
    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/bold red] {e}")


if __name__ == "__main__":
    main()
