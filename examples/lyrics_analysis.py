#!/usr/bin/env python
"""Example script demonstrating the Musixmatch client for lyrics analysis."""

import argparse
import os
import sys

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from flow_metrics.analysis.vocabulary import LyricsAnalyzer
from flow_metrics.clients.factory import create_musixmatch_client
from flow_metrics.clients.musixmatch import MusixmatchClient, MusixmatchError


def setup_argparse() -> argparse.ArgumentParser:
    """Set up command line argument parsing.

    Returns:
        Configured argument parser
    """
    parser = argparse.ArgumentParser(description="Analyze lyrics for an artist using Musixmatch")
    parser.add_argument("artist", help="Artist name to search for")
    parser.add_argument("--limit", type=int, default=5, help="Limit number of songs to analyze")
    return parser


def display_artist_info(client: MusixmatchClient, artist_name: str, console: Console) -> int:
    """Display artist information and return artist ID.

    Args:
        client: Musixmatch client
        artist_name: Artist name to search for
        console: Rich console

    Returns:
        Artist ID if found, or 0 if not found
    """
    console.print(f"[bold]Searching for artist:[/bold] {artist_name}")

    artists = client.search_artist(artist_name)

    if not artists:
        console.print("[bold red]Artist not found.[/bold red]")
        return 0

    # Display artists if multiple found
    if len(artists) > 1:
        console.print("[bold]Multiple artists found. Please select one:[/bold]")
        for i, artist in enumerate(artists, 1):
            console.print(f"{i}. {artist.artist_name} (Rating: {artist.artist_rating})")

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

    # Create a panel with artist info
    artist_info = [f"[bold]{artist.artist_name}[/bold]"]

    if artist.artist_country:
        artist_info.append(f"Country: {artist.artist_country}")

    artist_info.append(f"Rating: {artist.artist_rating}")

    if artist.artist_twitter_url:
        artist_info.append(f"Twitter: {artist.artist_twitter_url}")

    artist_panel = Panel("\n".join(artist_info))
    console.print(artist_panel)
    console.print()

    return artist.artist_id


def analyze_lyrics(client: MusixmatchClient, artist_id: int, limit: int, console: Console) -> None:
    """Analyze lyrics for an artist.

    Args:
        client: Musixmatch client
        artist_id: Musixmatch artist ID
        limit: Maximum number of songs to analyze
        console: Rich console
    """
    console.print("[bold]Getting tracks...[/bold]")

    # Get tracks by the artist
    tracks = client.get_all_artist_tracks(artist_id=artist_id, limit=limit)

    if not tracks:
        console.print("[bold red]No tracks found for this artist.[/bold red]")
        return

    console.print(f"[bold]Found {len(tracks)} tracks. Analyzing lyrics...[/bold]")
    console.print()

    # Initialize the lyrics analyzer
    analyzer = LyricsAnalyzer()

    # Analyze each track
    from typing import Any

    track_metrics: list[dict[str, Any]] = []
    success_count = 0

    for track in tracks:
        console.print(f"Analyzing: {track.track_name}")

        # Skip tracks without lyrics
        if track.has_lyrics == 0:
            console.print("  [yellow]No lyrics available for this track.[/yellow]")
            console.print()
            continue

        try:
            # Get lyrics
            lyrics_data = client.get_track_lyrics(track.track_id)
            lyrics = lyrics_data.lyrics_body

            # Musixmatch free API provides only 30% of the lyrics
            # Let the user know
            if "..." in lyrics:
                console.print(
                    "  [yellow]Note: Only partial lyrics available (Musixmatch API limitation)[/yellow]",  # noqa: E501
                )

            # Analyze lyrics
            metrics = analyzer.analyze_lyrics(lyrics)

            # Create a combined dictionary with track info and metrics
            track_data = {
                "track_title": track.track_name,
                "track_id": track.track_id,
                **metrics,  # Include all metrics
            }

            track_metrics.append(track_data)
            success_count += 1

            # Display metrics for this track
            console.print(f"  - Words: {int(metrics['total_words'])}")
            console.print(f"  - Unique Words: {int(metrics['unique_word_count'])}")
            console.print(f"  - Type-Token Ratio: {metrics['type_token_ratio']:.3f}")
            console.print(f"  - Average Word Length: {metrics['average_word_length']:.2f}")
            console.print(f"  - Lexical Density: {metrics['lexical_density']:.3f}")
            console.print()

        except MusixmatchError as e:
            console.print(f"  [bold red]Error:[/bold red] {e}")
            console.print()

    # Calculate average metrics across all tracks
    if track_metrics:
        avg_ttr = sum(m["type_token_ratio"] for m in track_metrics) / len(track_metrics)
        avg_awl = sum(m["average_word_length"] for m in track_metrics) / len(track_metrics)
        avg_ld = sum(m["lexical_density"] for m in track_metrics) / len(track_metrics)

        console.print(
            f"[bold]Successfully analyzed {success_count} out of {len(tracks)} tracks.[/bold]",
        )
        console.print("[bold]Average Metrics:[/bold]")
        console.print(f"Type-Token Ratio: {avg_ttr:.3f}")
        console.print(f"Average Word Length: {avg_awl:.2f}")
        console.print(f"Lexical Density: {avg_ld:.3f}")
    else:
        console.print("[bold red]Could not analyze any lyrics.[/bold red]")


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

        # Create Musixmatch client
        client = create_musixmatch_client()

        # Get artist info
        artist_id = display_artist_info(client, args.artist, console)

        if artist_id > 0:
            # Analyze lyrics
            analyze_lyrics(client, artist_id, args.limit, console)

    except MusixmatchError as e:
        console.print(f"[bold red]Musixmatch API Error:[/bold red] {e}")
    except KeyboardInterrupt:
        console.print("\n[bold]Operation cancelled.[/bold]")
    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/bold red] {e}")


if __name__ == "__main__":
    main()
