"""CLI-independent signing orchestration with immutable working copies."""

import shutil
import tempfile
from pathlib import Path

from projectseal.config import config_path, load_project
from projectseal.core.git import inspect_git
from projectseal.core.hashing import hash_file
from projectseal.core.manifest import create_manifest
from projectseal.exceptions import ProjectSealError
from projectseal.signing.base import SigningBackend
from projectseal.signing.cosign import Cosign
from projectseal.utils.files import check_output, publish_files, regular_file


def default_bundle(artifact: Path) -> Path:
    return Path(str(artifact) + ".sigstore.json")


def default_manifest(artifact: Path) -> Path:
    return Path(str(artifact) + ".manifest.json")


def sign_release(
    artifact: Path,
    *,
    output: Path | None = None,
    root: Path = Path("."),
    release_version: str | None = None,
    key: Path | None = None,
    non_interactive: bool = False,
    force: bool = False,
    backend: SigningBackend | None = None,
) -> dict[str, object]:
    source = regular_file(artifact)
    bundle = (output or default_bundle(artifact)).absolute()
    manifest_path = default_manifest(artifact).absolute()
    manifest_bundle = default_bundle(manifest_path)
    protected = (source, config_path(root)) + ((regular_file(key),) if key is not None else ())
    targets = [bundle]
    if release_version is not None:
        targets.extend([manifest_path, manifest_bundle])
    if len({p.resolve() for p in targets}) != len(targets):
        raise ProjectSealError("Release output paths conflict.", "OUTPUT_CONFLICT")
    for path in targets:
        check_output(path, protected, force)
    before = hash_file(source)
    project = load_project(root) if release_version is not None else None
    signer = backend if backend is not None else Cosign()
    with tempfile.TemporaryDirectory(prefix="projectseal-") as scratch:
        work = Path(scratch)
        snapshot = work / "artifact"
        shutil.copyfile(source, snapshot)
        snapshot_hash = hash_file(snapshot)
        if (snapshot_hash.digest, snapshot_hash.size) != (before.digest, before.size):
            raise ProjectSealError(
                "Artifact changed while copying; retry a stable file.", "FILE_MODIFIED"
            )
        staged_bundle = work / "bundle.json"
        signer.sign(snapshot, staged_bundle, key=key, non_interactive=non_interactive)
        files = {bundle: staged_bundle.read_bytes()}
        if project is not None and release_version is not None:
            before.file = str(artifact)
            manifest = create_manifest(project, release_version, before, inspect_git(root))
            staged_manifest = work / "manifest.json"
            staged_manifest.write_bytes(manifest.canonical_bytes())
            staged_evidence = work / "manifest.sigstore.json"
            signer.sign(staged_manifest, staged_evidence, key=key, non_interactive=non_interactive)
            files[manifest_path] = staged_manifest.read_bytes()
            files[manifest_bundle] = staged_evidence.read_bytes()
        after = hash_file(source)
        if (after.digest, after.size) != (before.digest, before.size):
            raise ProjectSealError(
                "Artifact changed during signing; no bundle was published.", "FILE_MODIFIED"
            )
        publish_files(files, force)
    return {
        "status": "SIGNED",
        "file": str(artifact),
        "sha256": before.digest,
        "bundle": str(bundle),
        "manifest": str(manifest_path) if project else None,
        "manifest_bundle": str(manifest_bundle) if project else None,
        "identity_verified": False,
        "message": "Bundle created. Verify it against an independently trusted identity or key.",
    }
