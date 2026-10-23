import hashlib
from pathlib import Path
from typing import Literal

from projectseal.config import Model
from projectseal.exceptions import ProjectSealError
from projectseal.utils.files import regular_file

CHUNK_SIZE = 1024 * 1024


class FileHash(Model):
    file: str
    algorithm: Literal["sha256"] = "sha256"
    digest: str
    size: int


def hash_file(path: Path) -> FileHash:
    source = regular_file(path)
    digest = hashlib.sha256()
    size = 0
    try:
        with source.open("rb") as stream:
            while chunk := stream.read(CHUNK_SIZE):
                digest.update(chunk)
                size += len(chunk)
    except OSError as exc:
        raise ProjectSealError(
            f"Cannot read {path}; check file permissions.", "FILE_ERROR"
        ) from exc
    return FileHash(file=str(path), digest=digest.hexdigest(), size=size)
