from typing import Any

from pydantic import BaseModel, Field, model_validator

from flow_metrics.models.musicbrainz import MusicBrainzReleaseGroup


class MusicBrainzReleaseGroupList(BaseModel):
    """List of MusicBrainz release groups."""

    count: int = Field(default=0, alias="release-group-count")
    offset: int = Field(default=0)
    release_groups: list[MusicBrainzReleaseGroup] = Field(
        alias="release-groups",
        default_factory=list,
    )

    class Config:
        populate_by_name = True
        from_attributes = True

    @model_validator(mode="before")
    @classmethod
    def validate_structure(cls, data: dict[str, Any]) -> dict[str, Any]:
        """Handle variations in API response structure."""
        # Handle both potential formats
        # If release-group-list exists, map it to release-groups
        if "release-group-list" in data:
            data["release-groups"] = data.pop("release-group-list")

        # Set default count and offset if not present
        if "count" in data and "release-group-count" not in data:
            data["release-group-count"] = data["count"]

        if "offset" not in data:
            data["offset"] = 0

        return data
