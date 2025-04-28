"""Pydantic models for MusicBrainz API responses."""

from typing import Any, TypeVar

from pydantic import BaseModel, Field

# Generic type for items in paginated responses
T = TypeVar("T")


class MusicBrainzError(Exception):
    """Custom exception for MusicBrainz API errors."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_data: dict[str, Any] | None = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(self.message)


class MusicBrainzLifeSpan(BaseModel):
    """Life span information for an artist or group."""

    begin: str | None = None
    end: str | None = None
    ended: bool | None = None


class MusicBrainzAlias(BaseModel):
    """Alias for an entity in MusicBrainz."""

    name: str
    sort_name: str | None = Field(None, alias="sort-name")
    type: str | None = None
    primary: bool | None = None
    begin_date: str | None = Field(None, alias="begin-date")
    end_date: str | None = Field(None, alias="end-date")
    locale: str | None = None

    class Config:
        populate_by_name = True


class MusicBrainzRelation(BaseModel):
    """Relation between entities in MusicBrainz."""

    type: str
    type_id: str = Field(alias="type-id")
    target_type: str = Field(alias="target-type")
    direction: str
    begin: str | None = None
    end: str | None = None
    ended: bool | None = None
    attribute_ids: dict[str, str] = Field(default_factory=dict, alias="attribute-ids")
    attributes: list[str] = Field(default_factory=list)
    attribute_values: dict[str, str] = Field(default_factory=dict, alias="attribute-values")

    # The target entity can be of various types
    # We'll handle this during parsing
    target_credit: str | None = Field(None, alias="target-credit")
    artist: dict[str, Any] | None = None
    work: dict[str, Any] | None = None
    recording: dict[str, Any] | None = None
    release: dict[str, Any] | None = None
    release_group: dict[str, Any] | None = Field(None, alias="release-group")

    class Config:
        populate_by_name = True


class MusicBrainzArea(BaseModel):
    """MusicBrainz area entity."""

    id: str
    name: str
    sort_name: str = Field(alias="sort-name")
    disambiguation: str | None = None
    iso_3166_1_codes: list[str] | None = Field(None, alias="iso-3166-1-codes")

    class Config:
        populate_by_name = True


class MusicBrainzArtistCredit(BaseModel):
    """Artist credit in MusicBrainz."""

    name: str
    artist: dict[str, Any]
    joinphrase: str | None = None


class MusicBrainzTag(BaseModel):
    """Tag for an entity in MusicBrainz."""

    count: int
    name: str


class MusicBrainzArtist(BaseModel):
    """MusicBrainz artist entity."""

    id: str
    name: str
    sort_name: str = Field(alias="sort-name")
    disambiguation: str | None = None
    type: str | None = None
    gender: str | None = None
    country: str | None = None
    score: int | None = Field(None, alias="ext:score")
    life_span: MusicBrainzLifeSpan | None = Field(None, alias="life-span")
    begin_area: MusicBrainzArea | None = Field(None, alias="begin-area")
    end_area: MusicBrainzArea | None = Field(None, alias="end-area")
    area: MusicBrainzArea | None = None
    ipis: list[str] | None = Field(None, alias="ipis")
    isnis: list[str] | None = Field(None, alias="isnis")
    aliases: list[MusicBrainzAlias] | None = Field(None, alias="alias-list")
    relations: list[MusicBrainzRelation] | None = Field(None, alias="relation-list")
    tags: list[MusicBrainzTag] | None = Field(None, alias="tag-list")

    class Config:
        populate_by_name = True


class MusicBrainzArtistList(BaseModel):
    """List of MusicBrainz artists."""

    count: int
    offset: int
    artists: list[MusicBrainzArtist] = Field(alias="artist-list")

    class Config:
        populate_by_name = True


class MusicBrainzReleaseGroup(BaseModel):
    """MusicBrainz release group entity."""

    id: str
    title: str
    primary_type: str | None = Field(None, alias="primary-type")
    primary_type_id: str | None = Field(None, alias="primary-type-id")
    secondary_types: list[str] | None = Field(None, alias="secondary-types")
    secondary_type_ids: list[str] | None = Field(None, alias="secondary-type-ids")
    first_release_date: str | None = Field(None, alias="first-release-date")
    disambiguation: str | None = None
    score: int | None = Field(None, alias="ext:score")
    artist_credit: list[MusicBrainzArtistCredit] | None = Field(None, alias="artist-credit")
    releases: list[dict[str, Any]] | None = Field(None, alias="release-list")
    tags: list[MusicBrainzTag] | None = Field(None, alias="tag-list")
    relations: list[MusicBrainzRelation] | None = Field(None, alias="relation-list")

    class Config:
        populate_by_name = True


class MusicBrainzReleaseGroupList(BaseModel):
    """List of MusicBrainz release groups."""

    count: int
    offset: int
    release_groups: list[MusicBrainzReleaseGroup] = Field(alias="release-group-list")

    class Config:
        populate_by_name = True


class MusicBrainzTrack(BaseModel):
    """MusicBrainz track entity."""

    id: str
    position: int
    number: str
    title: str
    length: int | None = None
    recording: dict[str, Any] | None = None
    artist_credit: list[MusicBrainzArtistCredit] | None = Field(None, alias="artist-credit")

    class Config:
        populate_by_name = True


class MusicBrainzMedium(BaseModel):
    """MusicBrainz medium entity (e.g., CD, vinyl)."""

    position: int
    format: str | None = None
    track_count: int = Field(alias="track-count")
    tracks: list[MusicBrainzTrack] | None = Field(None, alias="track-list")

    class Config:
        populate_by_name = True


class MusicBrainzCoverArtArchive(BaseModel):
    """Cover Art Archive metadata for a release."""

    artwork: bool
    count: int
    front: bool
    back: bool
    darkened: bool | None = None


class MusicBrainzLabelInfo(BaseModel):
    """Label information for a release."""

    catalog_number: str | None = Field(None, alias="catalog-number")
    label: dict[str, Any] | None = None

    class Config:
        populate_by_name = True


class MusicBrainzRelease(BaseModel):
    """MusicBrainz release entity."""

    id: str
    title: str
    status: str | None = None
    quality: str | None = None
    disambiguation: str | None = None
    packaging: str | None = None
    date: str | None = None
    country: str | None = None
    barcode: str | None = None
    score: int | None = Field(None, alias="ext:score")
    artist_credit: list[MusicBrainzArtistCredit] | None = Field(None, alias="artist-credit")
    release_group: dict[str, Any] | None = Field(None, alias="release-group")
    media: list[MusicBrainzMedium] | None = Field(None, alias="medium-list")
    label_info: list[MusicBrainzLabelInfo] | None = Field(None, alias="label-info-list")
    cover_art_archive: MusicBrainzCoverArtArchive | None = Field(None, alias="cover-art-archive")
    tags: list[MusicBrainzTag] | None = Field(None, alias="tag-list")
    relations: list[MusicBrainzRelation] | None = Field(None, alias="relation-list")

    class Config:
        populate_by_name = True


class MusicBrainzReleaseList(BaseModel):
    """List of MusicBrainz releases."""

    count: int
    offset: int
    releases: list[MusicBrainzRelease] = Field(alias="release-list")

    class Config:
        populate_by_name = True


class MusicBrainzRecording(BaseModel):
    """MusicBrainz recording entity."""

    id: str
    title: str
    length: int | None = None
    video: bool | None = None
    disambiguation: str | None = None
    score: int | None = Field(None, alias="ext:score")
    artist_credit: list[MusicBrainzArtistCredit] | None = Field(None, alias="artist-credit")
    releases: list[dict[str, Any]] | None = Field(None, alias="release-list")
    isrcs: list[str] | None = Field(None, alias="isrc-list")
    tags: list[MusicBrainzTag] | None = Field(None, alias="tag-list")
    relations: list[MusicBrainzRelation] | None = Field(None, alias="relation-list")

    class Config:
        populate_by_name = True


class MusicBrainzRecordingList(BaseModel):
    """List of MusicBrainz recordings."""

    count: int
    offset: int
    recordings: list[MusicBrainzRecording] = Field(alias="recording-list")

    class Config:
        populate_by_name = True


class MusicBrainzWork(BaseModel):
    """MusicBrainz work entity."""

    id: str
    title: str
    type: str | None = None
    disambiguation: str | None = None
    score: int | None = Field(None, alias="ext:score")
    language: str | None = None
    iswcs: list[str] | None = Field(None, alias="iswc-list")
    attributes: list[dict[str, Any]] | None = Field(None, alias="attribute-list")
    relations: list[MusicBrainzRelation] | None = Field(None, alias="relation-list")
    tags: list[MusicBrainzTag] | None = Field(None, alias="tag-list")

    class Config:
        populate_by_name = True


class MusicBrainzWorkList(BaseModel):
    """List of MusicBrainz works."""

    count: int
    offset: int
    works: list[MusicBrainzWork] = Field(alias="work-list")

    class Config:
        populate_by_name = True


class CoverArtImage(BaseModel):
    """Image from the Cover Art Archive."""

    id: str
    image: str
    approved: bool
    edit: int
    types: list[str]
    front: bool
    back: bool
    comment: str
    thumbnails: dict[str, str]


class CoverArtResponse(BaseModel):
    """Response from the Cover Art Archive."""

    images: list[CoverArtImage]
    release: str
