from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from projectseal.config import Author, Project, config_path
from projectseal.core.git import inspect_git
from projectseal.exceptions import ProjectSealError
from projectseal.utils.files import atomic_write, canonical_json


def initialize(
    root: Path, name: str | None = None, author: str = "Developer", website: str | None = None
) -> Project:
    path = config_path(root)
    if path.exists() or path.is_symlink():
        raise ProjectSealError(
            "Already initialized; existing identity was preserved.", "ALREADY_EXISTS"
        )
    project = Project(
        project_id=uuid4(),
        project_name=name or root.resolve().name,
        author=Author(display_name=author, website=website),
        repository=inspect_git(root).repository,
        created_at=datetime.now(UTC),
    )
    path.parent.mkdir(exist_ok=True)
    ignore = path.parent / ".gitignore"
    if not ignore.exists():
        atomic_write(ignore, b"# Local release state; never commit private keys.\n*\n")
    atomic_write(path, canonical_json(project.model_dump(mode="json")) + b"\n")
    return project
