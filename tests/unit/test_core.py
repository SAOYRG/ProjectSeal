import hashlib
import io
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from projectseal.config import config_path, load_policy, load_project
from projectseal.core.git import GitInfo, inspect_git, safe_remote
from projectseal.core.hashing import CHUNK_SIZE, hash_file
from projectseal.core.identity import initialize
from projectseal.core.manifest import Manifest, create_manifest
from projectseal.exceptions import ProjectSealError
from projectseal.utils.files import atomic_write, canonical_json, read_json


@pytest.mark.parametrize(
    "data",
    [b"", b"hello", b"\x00\xff" * 30, b"x" * (CHUNK_SIZE * 5 + 7)],
    ids=["empty", "text", "binary", "large"],
)
def test_hash_vectors(tmp_path, data):
    path = tmp_path / "input"
    path.write_bytes(data)
    first = hash_file(path)
    assert first.digest == hashlib.sha256(data).hexdigest()
    assert first.size == len(data)
    assert hash_file(path) == first
    path.write_bytes(data + b"!")
    assert hash_file(path).digest != first.digest


def test_streaming_reads_are_bounded(artifact, monkeypatch):
    original = Path.open
    calls = []

    class Bounded(io.BytesIO):
        def read(self, size=-1):
            calls.append(size)
            assert 0 < size <= CHUNK_SIZE
            return super().read(size)

    def open_file(path, *args, **kwargs):
        return (
            Bounded(b"x" * (CHUNK_SIZE + 1))
            if path == artifact
            else original(path, *args, **kwargs)
        )

    monkeypatch.setattr(Path, "open", open_file)
    assert hash_file(artifact).size == CHUNK_SIZE + 1
    assert len(calls) == 3


@pytest.mark.parametrize("kind", ["missing", "directory"])
def test_hash_non_file(tmp_path, kind):
    with pytest.raises(ProjectSealError, match="regular file"):
        hash_file(tmp_path if kind == "directory" else tmp_path / "missing")


def test_identity_unicode_nongit_and_no_overwrite(tmp_path):
    root = tmp_path / "中文 project & space"
    root.mkdir()
    project = initialize(root, "测试", "Developer", "https://example.com")
    assert project.project_name == "测试"
    assert project.created_at.utcoffset().total_seconds() == 0
    assert load_project(root) == project
    assert project.repository is None
    original = config_path(root).read_bytes()
    with pytest.raises(ProjectSealError, match="Already initialized"):
        initialize(root)
    assert config_path(root).read_bytes() == original
    assert (root / ".projectseal" / ".gitignore").exists()


@pytest.mark.parametrize(
    "mutation",
    [
        {"schema_version": "2.0"},
        {"project_id": "bad"},
        {"project_name": ""},
        {"unknown": True},
        {"created_at": "2026-10-24T00:00:00"},
        {"author": {"display_name": 123}},
        {"author": {"display_name": "Dev", "website": "file:///secret"}},
    ],
)
def test_invalid_config(tmp_path, mutation):
    initialize(tmp_path)
    data = read_json(config_path(tmp_path))
    data.update(mutation)
    config_path(tmp_path).write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ProjectSealError, match="Invalid"):
        load_project(tmp_path)


@pytest.mark.parametrize("raw", [b"{broken", b'{"x":1,"x":2}', b"\xff", b"[" * 2000])
def test_invalid_json(tmp_path, raw):
    path = tmp_path / "config.json"
    path.write_bytes(raw)
    with pytest.raises(ProjectSealError):
        read_json(path)


def test_json_size_bound(tmp_path):
    path = tmp_path / "large.json"
    path.write_bytes(b" " * 101)
    with pytest.raises(ProjectSealError):
        read_json(path, limit=100)


def test_atomic_write_no_clobber(tmp_path):
    path = tmp_path / "identity"
    atomic_write(path, b"one")
    with pytest.raises(ProjectSealError):
        atomic_write(path, b"two")
    assert path.read_bytes() == b"one"
    atomic_write(path, b"two", force=True)
    assert path.read_bytes() == b"two"


def test_manifest_canonical(tmp_path, artifact):
    project = initialize(tmp_path)
    manifest = create_manifest(project, "0.1.0", hash_file(artifact), GitInfo())
    raw = manifest.canonical_bytes()
    assert b"\n" not in raw
    assert Manifest.model_validate(json.loads(raw)).canonical_bytes() == raw
    assert canonical_json({"b": 1, "a": "中"}) == canonical_json({"a": "中", "b": 1})


@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://user:secret@example.com/a.git?token=secret#x", "https://example.com/a.git"),
        ("git@github.com:user/repo.git", "ssh://github.com/user/repo.git"),
        ("F:\\private\\repo", None),
        ("nonsense", None),
    ],
)
def test_git_remote_redaction(url, expected):
    assert safe_remote(url) == expected


def test_missing_git_is_optional(tmp_path, monkeypatch):
    monkeypatch.setattr("projectseal.core.git.shutil.which", lambda _: None)
    assert not inspect_git(tmp_path).available


def test_policy_is_explicit_validated(tmp_path, policy):
    path = tmp_path / "trusted.json"
    path.write_bytes(canonical_json(policy.model_dump(mode="json")))
    assert load_policy(path) == policy
    path.write_text('{"certificate_identity":".*"}', encoding="utf-8")
    with pytest.raises(ProjectSealError):
        load_policy(path)
    with pytest.raises(ValidationError):
        type(policy)(certificate_identity="a\nb", certificate_oidc_issuer="https://example.com")
