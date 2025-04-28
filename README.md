# FlowMetrics

FlowMetrics is a Python application for analyzing hip-hop artist vocabulary and career metrics using data from multiple music APIs.

## Project Overview

This project aims to create a comprehensive analysis of hip-hop artists' vocabulary richness and career metrics by:

1. Collecting data from multiple APIs (Spotify, MusicBrainz, Genius)
2. Analyzing lyrics for vocabulary metrics
3. Correlating vocabulary richness with career success metrics

## Features

- Comprehensive Spotify API client with Pydantic models
- Lyrics analysis tools for vocabulary metrics computation
- Artist discography and timeline visualization
- Correlation analysis between vocabulary metrics and career success

## Installation

### Prerequisites

- Python 3.12+
- Poetry (dependency management)

### Setup

1. Clone the repository:

```bash
git clone https://github.com/yourusername/flow-metrics.git
cd flow-metrics
```

2. Install dependencies with Poetry:

```bash
poetry install
```

3. Create a `.env` file in the project root with your API credentials:

```bash
# Spotify API credentials
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret

# Genius API credentials (optional for lyrics)
GENIUS_ACCESS_TOKEN=your_genius_access_token
```

## Usage

### Command Line Interface

The project includes a command-line tool for artist analysis:

```bash
# Activate the Poetry environment
poetry shell

# Search for an artist and display their basic info
python examples/artist_analysis.py "Kendrick Lamar"

# Show top tracks
python examples/artist_analysis.py "Kendrick Lamar" --top-tracks

# Show release timeline
python examples/artist_analysis.py "Kendrick Lamar" --timeline

# Filter by album type
python examples/artist_analysis.py "Kendrick Lamar" --timeline --album-type album single
```

### Python API

You can also use the library in your own Python code:

```python
from flow_metrics.clients.factory import create_spotify_client
from flow_metrics.analysis.vocabulary import LyricsAnalyzer

# Create a Spotify client
spotify = create_spotify_client()

# Search for an artist
artists = spotify.search_artists("Kendrick Lamar")
artist = artists[0]

# Get artist stats
stats = spotify.get_artist_stats(artist.id)

# Get all artist tracks
tracks = spotify.get_artist_all_tracks(artist.id, album_types=["album"])

# Analyze lyrics (requires integration with a lyrics API)
lyrics_analyzer = LyricsAnalyzer()
metrics = lyrics_analyzer.analyze_lyrics(lyrics_text)
```

## Project Structure

```
flow-metrics/
├── flow_metrics/             # Main package
│   ├── http/                 # HTTP client
│   ├── clients/              # API clients (Spotify, MusicBrainz, Genius)
│   ├── models/               # Pydantic models
│   ├── analysis/             # Analysis tools
│   ├── config/               # Configuration
│   └── utils/                # Utilities
├── examples/                 # Example scripts
├── tests/                    # Unit tests
├── pyproject.toml            # Poetry configuration
└── README.md                 # This file
```

## Development

### Running Tests

```bash
poetry run pytest
```

### Linting and Formatting

The project uses Ruff for both linting and formatting:

```bash
# Check code
poetry run ruff check .

# Format code
poetry run ruff format .
```

### Type Checking

The project uses Pyright for static type checking:

```bash
poetry run pyright
```

### Pre-commit Hooks

Install pre-commit hooks to automatically run linting and type checking before commits:

```bash
poetry run pre-commit install
```

## Future Work

- MusicBrainz API integration for additional metadata
- Genius API integration for lyrics collection
- Database storage for collected data
- Web dashboard for visualization
- Machine learning models for vocabulary analysis

## License

MIT