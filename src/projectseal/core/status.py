from pathlib import Path

from projectseal.config import config_path, load_project
from projectseal.core.git import inspect_git


def project_status(root: Path) -> dict[str, object]:
    """Read local project/Git state and bounded, explicitly untrusted release references."""
    initialized = config_path(root).exists()
    releases = sorted(
        str(path.relative_to(root))
        for folder in (root, root / "dist", root / "releases")
        if folder.is_dir()
        for path in folder.glob("*.manifest.json")
        if path.is_file()
    )
    return {
        "initialized": initialized,
        "project": load_project(root).model_dump(mode="json") if initialized else None,
        "git": inspect_git(root).as_dict(),
        "release_manifests": releases,
        "release_claims_authenticated": False,
    }
