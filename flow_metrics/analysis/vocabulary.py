"""Vocabulary analysis utilities."""

import re
import string

import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import (
    word_tokenize,  # type: ignore
)


# Ensure required NLTK data is downloaded
def download_nltk_data() -> None:
    """Download required NLTK data if not already present."""
    try:
        nltk.data.find("tokenizers/punkt")  # type: ignore
    except LookupError:
        nltk.download("punkt")  # type: ignore

    try:
        nltk.data.find("corpora/stopwords")  # type: ignore
    except LookupError:
        nltk.download("stopwords")  # type: ignore

    try:
        nltk.data.find("corpora/wordnet")  # type: ignore
    except LookupError:
        nltk.download("wordnet")  # type: ignore


class LyricsAnalyzer:
    """Analyze lyrics for vocabulary metrics."""

    def __init__(self) -> None:
        """Initialize the lyrics analyzer."""
        download_nltk_data()
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words("english"))  # type: ignore

        # Add common lyrics section headers to filter out
        self.section_headers = {
            "verse",
            "verse 1",
            "verse 2",
            "verse 3",
            "verse 4",
            "chorus",
            "bridge",
            "outro",
            "intro",
            "hook",
            "pre-chorus",
            "refrain",
            "interlude",
            "ad libs",
            "breakdown",
        }

    def clean_lyrics(self, lyrics: str) -> str:
        """Clean lyrics by removing section headers, punctuation, etc.

        Args:
            lyrics: Raw lyrics text

        Returns:
            Cleaned lyrics text
        """
        # Convert to lowercase
        text = lyrics.lower()

        # Remove timestamps like [0:42]
        text = re.sub(r"\[\d+:\d+\]", "", text)

        # Remove section headers like [Verse 1] or [Chorus]
        text = re.sub(r"\[(.*?)\]", "", text)

        # Remove parenthetical annotations like (x2) or (repeat)
        text = re.sub(r"\(.*?\)", "", text)

        # Remove punctuation
        text = text.translate(str.maketrans("", "", string.punctuation))

        # Remove extra whitespace
        return re.sub(r"\s+", " ", text).strip()

    def tokenize_lyrics(self, lyrics: str) -> list[str]:
        """Tokenize lyrics into words.

        Args:
            lyrics: Cleaned lyrics text

        Returns:
            List of words
        """
        return word_tokenize(lyrics)

    def filter_words(self, words: list[str]) -> list[str]:
        """Filter out stop words and non-content words.

        Args:
            words: List of tokenized words

        Returns:
            Filtered list of words
        """
        # Filter out stop words, section headers, and single characters
        return [
            word
            for word in words
            if word not in self.stop_words and word not in self.section_headers and len(word) > 1
        ]

    def lemmatize_words(self, words: list[str]) -> list[str]:
        """Lemmatize words to their root form.

        Args:
            words: List of words

        Returns:
            List of lemmatized words
        """
        return [self.lemmatizer.lemmatize(word) for word in words]

    def analyze_lyrics(self, lyrics: str) -> dict[str, float]:
        """Analyze lyrics and compute vocabulary metrics.

        Args:
            lyrics: Raw lyrics text

        Returns:
            Dictionary of vocabulary metrics
        """
        # Clean the lyrics
        cleaned_text = self.clean_lyrics(lyrics)

        # Tokenize
        tokens = self.tokenize_lyrics(cleaned_text)

        # Get all words (including duplicates)
        all_words = [token for token in tokens if token.isalpha()]

        # Filter out stop words for content words
        filtered_words = self.filter_words(all_words)

        # Lemmatize words to count word roots instead of variations
        lemmatized_words = self.lemmatize_words(filtered_words)

        # Get unique words
        unique_words = set(lemmatized_words)

        # Calculate metrics
        total_words = len(all_words)
        unique_word_count = len(unique_words)

        # Type-Token Ratio (TTR) - ratio of unique words to total words
        ttr = unique_word_count / total_words if total_words > 0 else 0

        # Average Word Length (AWL)
        total_length = sum(len(word) for word in all_words)
        awl = total_length / total_words if total_words > 0 else 0

        # Lexical Density (LD) - ratio of content words to total words
        content_words_count = len(filtered_words)
        ld = content_words_count / total_words if total_words > 0 else 0

        return {
            "total_words": float(total_words),
            "unique_word_count": float(unique_word_count),
            "type_token_ratio": ttr,
            "average_word_length": awl,
            "lexical_density": ld,
        }

    def calculate_vocabulary_richness(
        self,
        artist_metrics: dict[str, float],
        baseline_metrics: dict[str, float],
    ) -> float:
        """Calculate vocabulary richness compared to baseline.

        Args:
            artist_metrics: Dictionary of artist vocabulary metrics
            baseline_metrics: Dictionary of baseline vocabulary metrics

        Returns:
            Vocabulary richness score (percentage above/below baseline)
        """
        # Compare TTR with baseline
        artist_ttr = artist_metrics["type_token_ratio"]
        baseline_ttr = baseline_metrics["type_token_ratio"]

        # Calculate percentage difference
        return (artist_ttr - baseline_ttr) / baseline_ttr * 100 if baseline_ttr > 0 else 0
