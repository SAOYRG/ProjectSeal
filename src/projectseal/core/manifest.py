"""ProjectSeal manifest 1.0; canonical UTF-8 bytes are signed as a separate blob."""

from datetime import UTC, datetime
from pathlib import Path
from typing import Literal
from uuid import UUID

from pydantic import Field, field_validator

from projectseal.config import Model, Project
from projectseal.core.git import GitInfo
from projectseal.core.hashing import FileHash
from projectseal.utils.files import canonical_json


class Artifact(Model):
    filename: str = Field(min_length=1, max_length=255)
    size: int = Field(ge=0, strict=True)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @field_validator("filename")
    @classmethod
    def basename_only(cls, value: str) -> str:
        if "/" in value or "\\" in value or value in {".", ".."}:
            raise ValueError("filename must be a basename")
        return value


class Source(Model):
    git_commit: str | None = Field(default=None, pattern=r"^[0-9a-f]{40,64}$")
    repository: str | None = None


class Manifest(Model):
    schema_version: Literal["1.0"] = "1.0"
    project_id: UUID
    project_name: str = Field(min_length=1, max_length=200)
    version: str = Field(min_length=1, max_length=100)
    artifact: Artifact
    source: Source
    created_at: datetime

    @field_validator("created_at")
    @classmethod
    def utc_timestamp(cls, value: datetime) -> datetime:
        return Project.utc_timestamp(value)

    def canonical_bytes(self) -> bytes:
        return canonical_json(self.model_dump(mode="json"))


def create_manifest(project: Project, version: str, file: FileHash, git: GitInfo) -> Manifest:
    return Manifest(
        project_id=project.project_id,
        project_name=project.project_name,
        version=version,
        artifact=Artifact(filename=Path(file.file).name, size=file.size, sha256=file.digest),
        source=Source(git_commit=git.commit, repository=git.repository or project.repository),
        created_at=datetime.now(UTC),
    )
