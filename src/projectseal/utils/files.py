"""Strict JSON and atomic local file operations."""

import json
import os
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from projectseal.exceptions import ProjectSealError


def regular_file(path: Path) -> Path:
    if not path.is_file():
        raise ProjectSealError(f"Not a readable regular file: {path}", "FILE_ERROR")
    return path.resolve()


def _unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON field")
        result[key] = value
    return result


def read_json(path: Path, limit: int = 4 * 1024 * 1024) -> Any:
    try:
        with regular_file(path).open("rb") as stream:
            raw = stream.read(limit + 1)
        if len(raw) > limit:
            raise ValueError("JSON file exceeds size limit")
        return json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_pairs)
    except (OSError, ValueError, RecursionError) as exc:
        raise ProjectSealError(
            f"Cannot read valid JSON from {path}; repair the file or restore a backup.",
            "JSON_ERROR",
        ) from exc


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def check_output(path: Path, protected: tuple[Path, ...] = (), force: bool = False) -> None:
    if path.is_symlink():
        raise ProjectSealError(f"Refusing symbolic link output: {path}", "OUTPUT_EXISTS")
    resolved = path.resolve()
    for source in protected:
        if resolved == source.resolve() or (
            path.exists() and source.exists() and path.samefile(source)
        ):
            raise ProjectSealError("An output would overwrite an input file.", "OUTPUT_CONFLICT")
    if path.exists() and (not force or not path.is_file()):
        raise ProjectSealError(
            f"Output exists: {path}. Use --force to replace it.", "OUTPUT_EXISTS"
        )
    if not path.parent.is_dir():
        raise ProjectSealError(f"Output directory does not exist: {path.parent}", "FILE_ERROR")


def atomic_write(path: Path, data: bytes, force: bool = False) -> None:
    check_output(path, force=force)
    staged: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
            staged = Path(stream.name)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        if force:
            os.replace(staged, path)
        elif os.name == "nt":
            # Windows rename fails if the destination exists; no hard-link privilege required.
            os.rename(staged, path)
        else:
            # Hard-link publication is atomic and never clobbers a concurrently created file.
            os.link(staged, path)
    except OSError as exc:
        raise ProjectSealError(
            f"Cannot publish {path}; check permissions, free space and existing files.",
            "FILE_ERROR",
        ) from exc
    finally:
        if staged is not None:
            staged.unlink(missing_ok=True)


def publish_files(files: Mapping[Path, bytes], force: bool = False) -> None:
    """Publish a small release set; restore previous bytes on ordinary I/O failure.

    This is not a filesystem transaction across process crashes. Each file is atomic.
    """
    for path in files:
        check_output(path, force=force)
    old = {p: p.read_bytes() if p.exists() else None for p in files}
    written: list[Path] = []
    try:
        for path, data in files.items():
            atomic_write(path, data, force)
            written.append(path)
    except ProjectSealError:
        for path in reversed(written):
            previous = old[path]
            if previous is None:
                path.unlink(missing_ok=True)
            else:
                atomic_write(path, previous, force=True)
        raise
