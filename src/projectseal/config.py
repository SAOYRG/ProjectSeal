"""Versioned, language-independent project identity and explicit trust policy models."""

from datetime import UTC, datetime
from pathlib import Path
from typing import Literal, Self
from urllib.parse import urlsplit
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from projectseal.exceptions import ProjectSealError
from projectseal.utils.files import read_json


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Author(Model):
    display_name: str = Field(min_length=1, max_length=200)
    website: str | None = None

    @field_validator("website")
    @classmethod
    def validate_website(cls, value: str | None) -> str | None:
        if value is not None:
            parsed = urlsplit(value)
            if parsed.scheme not in {"https", "http"} or not parsed.hostname or parsed.username:
                raise ValueError("website must be an HTTP(S) URL without credentials")
        return value


class Project(Model):
    schema_version: Literal["1.0"] = "1.0"
    project_id: UUID
    project_name: str = Field(min_length=1, max_length=200)
    author: Author
    repository: str | None = None
    created_at: datetime

    @field_validator("created_at")
    @classmethod
    def utc_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("timestamp must include timezone")
        return value.astimezone(UTC)


class TrustPolicy(Model):
    schema_version: Literal["1.0"] = "1.0"
    certificate_identity: str = Field(min_length=1, max_length=2048)
    certificate_oidc_issuer: str = Field(min_length=1, max_length=2048)

    @model_validator(mode="after")
    def exact_values(self) -> Self:
        if any(ord(c) < 32 for c in self.certificate_identity + self.certificate_oidc_issuer):
            raise ValueError("control characters are forbidden")
        if not self.certificate_oidc_issuer.startswith("https://"):
            raise ValueError("OIDC issuer must be an HTTPS URL")
        return self


def config_path(root: Path) -> Path:
    return root / ".projectseal" / "project.json"


def load_project(root: Path) -> Project:
    path = config_path(root)
    if not path.exists():
        raise ProjectSealError("Project not initialized. Run projectseal init.", "NOT_INITIALIZED")
    try:
        return Project.model_validate(read_json(path))
    except ValidationError as exc:
        raise ProjectSealError(
            "Invalid .projectseal/project.json; repair it or restore a backup.", "CONFIG_ERROR"
        ) from exc


def load_policy(path: Path) -> TrustPolicy:
    try:
        return TrustPolicy.model_validate(read_json(path))
    except ValidationError as exc:
        raise ProjectSealError(
            "Invalid trust policy; use exact identity and HTTPS issuer.", "CONFIG_ERROR"
        ) from exc
