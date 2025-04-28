#!/usr/bin/env python
"""Example script demonstrating the Lyrics Scraper for lyrics analysis."""

import argparse
import os
import sys
from typing import Any

from dotenv import load_dotenv
from rich.console import Console

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from flow_metrics.analysis.vocabulary import LyricsAnalyzer
from flow_metrics.clients.lyrics_scraper import LyricsScraper
from flow_metrics.models.lyrics import LyricsScraperError


def setup_argparse() -> argparse.ArgumentParser:
    """Set up command line argument parsing.

    Returns:
        Configured argument parser
    """
    parser = argparse.ArgumentParser(description="Analyze lyrics for an artist using web scraping")
    parser.add_argument("artist", help="Artist name to search for")
    parser.add_argument("--limit", type=int, default=5, help="Limit number of songs to analyze")
    return parser


def analyze_artist_lyrics(
    scraper: LyricsScraper,
    artist_name: str,
    limit: int,
    console: Console,
) -> None:
    """Analyze lyrics for an artist.

    Args:
        scraper: Lyrics scraper
        artist_name: Artist name
        limit: Maximum number of songs to scrape
        console: Rich console
    """
    console.print(f"[bold]Searching for songs by:[/bold] {artist_name}")

    try:
        # Get songs and lyrics
        lyrics_list = scraper.get_artist_lyrics(artist_name, max_songs=limit)

        if not lyrics_list:
            console.print("[bold red]No songs found for this artist.[/bold red]")
            return

        console.print(f"[bold]Found {len(lyrics_list)} songs with lyrics. Analyzing...[/bold]")
        console.print()

        # Initialize lyrics analyzer
        analyzer = LyricsAnalyzer()

        # Analyze each song's lyrics
        song_metrics: list[dict[str, Any]] = []

        for lyrics_data in lyrics_list:
            console.print(f"Analyzing: {lyrics_data.title}")

            try:
                # Analyze lyrics
                metrics: dict[str, Any] = analyzer.analyze_lyrics(lyrics_data.lyrics)

                # Add song info to metrics
                metrics["song_title"] = lyrics_data.title
                metrics["source"] = lyrics_data.source

                song_metrics.append(metrics)

                # Display metrics for this song
                console.print(f"  - Words: {int(metrics['total_words'])}")
                console.print(f"  - Unique Words: {int(metrics['unique_word_count'])}")
                console.print(f"  - Type-Token Ratio: {metrics['type_token_ratio']:.3f}")
                console.print(f"  - Average Word Length: {metrics['average_word_length']:.2f}")
                console.print(f"  - Lexical Density: {metrics['lexical_density']:.3f}")
                console.print()

            except Exception as e:
                console.print(f"  [bold red]Error analyzing lyrics:[/bold red] {e}")
                console.print()

        # Calculate average metrics across all songs
        if song_metrics:
            avg_ttr = sum(m["type_token_ratio"] for m in song_metrics) / len(song_metrics)
            avg_awl = sum(m["average_word_length"] for m in song_metrics) / len(song_metrics)
            avg_ld = sum(m["lexical_density"] for m in song_metrics) / len(song_metrics)

            console.print("[bold]Average Metrics:[/bold]")
            console.print(f"Type-Token Ratio: {avg_ttr:.3f}")
            console.print(f"Average Word Length: {avg_awl:.2f}")
            console.print(f"Lexical Density: {avg_ld:.3f}")
        else:
            console.print("[bold red]Could not analyze any lyrics.[/bold red]")

    except LyricsScraperError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")


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

        # Create lyrics scraper with conservative rate limit
        scraper = LyricsScraper(rate_limit=3.0)

        # Analyze artist lyrics
        analyze_artist_lyrics(scraper, args.artist, args.limit, console)

    except LyricsScraperError as e:
        console.print(f"[bold red]Lyrics Scraper Error:[/bold red] {e}")
    except KeyboardInterrupt:
        console.print("\n[bold]Operation cancelled.[/bold]")
    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/bold red] {e}")


if __name__ == "__main__":
    main()
