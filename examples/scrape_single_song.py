#!/usr/bin/env python
"""Script for searching and analyzing lyrics for a specific song."""

import argparse
import os
import sys

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel

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
    parser = argparse.ArgumentParser(description="Analyze lyrics for a specific song")
    parser.add_argument("artist", help="Artist name")
    parser.add_argument("title", help="Song title")
    return parser


def analyze_song_lyrics(scraper: LyricsScraper, artist: str, title: str, console: Console) -> None:
    """Analyze lyrics for a specific song.

    Args:
        scraper: Lyrics scraper
        artist: Artist name
        title: Song title
        console: Rich console
    """
    console.print(f"[bold]Searching for:[/bold] {artist} - {title}")

    try:
        # Get lyrics
        lyrics_data = scraper.get_song_lyrics(artist, title)

        console.print(f"[bold]Found lyrics from {lyrics_data.source}. Analyzing...[/bold]")
        console.print()

        # Show a sample of the lyrics
        lyrics_sample = lyrics_data.lyrics.split("\n")
        if len(lyrics_sample) > 10:
            lyrics_sample = lyrics_sample[:10] + ["..."]

        lyrics_panel = Panel(
            "\n".join(lyrics_sample),
            title=f"{lyrics_data.artist} - {lyrics_data.title}",
            subtitle=f"Source: {lyrics_data.source}",
        )
        console.print(lyrics_panel)
        console.print()

        # Initialize lyrics analyzer
        analyzer = LyricsAnalyzer()

        # Analyze lyrics
        metrics = analyzer.analyze_lyrics(lyrics_data.lyrics)

        # Display metrics
        console.print("[bold]Lyrics Analysis:[/bold]")
        console.print(f"Total Words: {int(metrics['total_words'])}")
        console.print(f"Unique Words: {int(metrics['unique_word_count'])}")
        console.print(f"Type-Token Ratio: {metrics['type_token_ratio']:.3f}")
        console.print(f"Average Word Length: {metrics['average_word_length']:.2f}")
        console.print(f"Lexical Density: {metrics['lexical_density']:.3f}")

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

        # Analyze song lyrics
        analyze_song_lyrics(scraper, args.artist, args.title, console)

    except LyricsScraperError as e:
        console.print(f"[bold red]Lyrics Scraper Error:[/bold red] {e}")
    except KeyboardInterrupt:
        console.print("\n[bold]Operation cancelled.[/bold]")
    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/bold red] {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
