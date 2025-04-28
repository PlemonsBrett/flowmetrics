"""MongoDB utilities for Flow Metrics."""

from typing import Any

from pymongo import MongoClient
from pymongo.collection import Collection

from flow_metrics.config.settings import get_settings


class MongoDBClient:
    """MongoDB client for Flow Metrics data storage."""

    def __init__(
        self,
        uri: str | None = None,
        db_name: str | None = None,
        collection_name: str | None = None,
    ) -> None:
        """Initialize MongoDB client.

        Args:
            uri: MongoDB connection URI (if None, uses settings)
            db_name: Database name (if None, uses settings)
            collection_name: Default collection name (if None, uses settings)
        """
        settings = get_settings()
        self.uri = uri or settings.mongo_uri
        self.db_name = db_name or settings.mongo_db
        self.default_collection = collection_name or settings.mongo_collection

        self.client = MongoClient(self.uri)
        self.db = self.client[self.db_name]

    def get_collection(self, collection_name: str | None = None) -> Collection:
        """Get a MongoDB collection.

        Args:
            collection_name: Collection name (if None, uses default)

        Returns:
            MongoDB collection
        """
        return self.db[collection_name or self.default_collection]

    def insert_artist(
        self,
        artist_data: dict[str, Any],
        collection_name: str | None = None,
    ) -> str:
        """Insert artist data into MongoDB.

        Args:
            artist_data: Artist data to insert
            collection_name: Collection name (if None, uses default)

        Returns:
            ID of the inserted document
        """
        collection = self.get_collection(collection_name)
        result = collection.insert_one(artist_data)
        return str(result.inserted_id)

    def update_artist(
        self,
        spotify_id: str,
        artist_data: dict[str, Any],
        collection_name: str | None = None,
    ) -> int:
        """Update artist data in MongoDB.

        Args:
            spotify_id: Spotify artist ID
            artist_data: Updated artist data
            collection_name: Collection name (if None, uses default)

        Returns:
            Number of documents modified
        """
        collection = self.get_collection(collection_name)
        result = collection.update_one(
            {"spotify_id": spotify_id},
            {"$set": artist_data},
        )
        return result.modified_count

    def upsert_artist(
        self,
        artist_data: dict[str, Any],
        collection_name: str | None = None,
    ) -> dict[str, Any]:
        """Insert or update artist data in MongoDB.

        Args:
            artist_data: Artist data
            collection_name: Collection name (if None, uses default)

        Returns:
            Dictionary with operation result info
        """
        collection = self.get_collection(collection_name)

        # Check if artist already exists
        existing = collection.find_one({"spotify_id": artist_data["spotify_id"]})

        if existing:
            # Update existing document
            result = collection.update_one(
                {"spotify_id": artist_data["spotify_id"]},
                {"$set": artist_data},
            )
            return {
                "operation": "update",
                "modified_count": result.modified_count,
                "_id": existing["_id"],
            }
        # Insert new document
        result = collection.insert_one(artist_data)
        return {
            "operation": "insert",
            "inserted_id": result.inserted_id,
        }

    def find_artist_by_spotify_id(
        self,
        spotify_id: str,
        collection_name: str | None = None,
    ) -> dict[str, Any] | None:
        """Find artist by Spotify ID.

        Args:
            spotify_id: Spotify artist ID
            collection_name: Collection name (if None, uses default)

        Returns:
            Artist data or None if not found
        """
        collection = self.get_collection(collection_name)
        return collection.find_one({"spotify_id": spotify_id})

    def find_artist_by_name(
        self,
        name: str,
        collection_name: str | None = None,
    ) -> list[dict[str, Any]]:
        """Find artists by name (case-insensitive).

        Args:
            name: Artist name
            collection_name: Collection name (if None, uses default)

        Returns:
            List of matching artists
        """
        collection = self.get_collection(collection_name)
        return list(collection.find({"name": {"$regex": name, "$options": "i"}}))

    def find_artists_by_genre(
        self,
        genre: str,
        collection_name: str | None = None,
    ) -> list[dict[str, Any]]:
        """Find artists by genre (case-insensitive).

        Args:
            genre: Genre to search for
            collection_name: Collection name (if None, uses default)

        Returns:
            List of matching artists
        """
        collection = self.get_collection(collection_name)
        return list(collection.find({"genres": {"$regex": genre, "$options": "i"}}))

    def count_artists(self, collection_name: str | None = None) -> int:
        """Count the number of artists in the collection.

        Args:
            collection_name: Collection name (if None, uses default)

        Returns:
            Number of artists
        """
        collection = self.get_collection(collection_name)
        return collection.count_documents({})
