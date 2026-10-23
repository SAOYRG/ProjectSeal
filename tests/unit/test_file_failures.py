import os
from pathlib import Path

import pytest
from typer.testing import CliRunner

from projectseal.cli import app
from projectseal.core.hashing import hash_file
from projectseal.exceptions import Cancelled, ProjectSealError
from projectseal.utils.files import atomic_write, check_output, publish_files


def test_publication_race_never_clobbers(tmp_path, monkeypatch):
    target = tmp_path / "bundle"
    method = "rename" if os.name == "nt" else "link"
    original = getattr(os, method)

    def competing_writer(source, destination):
        Path(destination).write_bytes(b"other process")
        return original(source, destination)

    monkeypatch.setattr(f"projectseal.utils.files.os.{method}", competing_writer)
    with pytest.raises(ProjectSealError):
        atomic_write(target, b"our bundle")
    assert target.read_bytes() == b"other process"


@pytest.mark.parametrize("previous", [None, b"old bundle"])
def test_partial_release_failure_rolls_back(tmp_path, monkeypatch, previous):
    from projectseal.utils.files import atomic_write as actual_write

    first, second = tmp_path / "bundle", tmp_path / "manifest"
    if previous is not None:
        first.write_bytes(previous)

    def fail_second(path, data, force=False):
        if path == second:
            raise ProjectSealError("simulated disk failure")
        actual_write(path, data, force)

    monkeypatch.setattr("projectseal.utils.files.atomic_write", fail_second)
    with pytest.raises(ProjectSealError):
        publish_files({first: b"new bundle", second: b"new manifest"}, force=True)
    assert first.read_bytes() == previous if previous is not None else not first.exists()
    assert not second.exists()


def test_permission_error_is_actionable(artifact, monkeypatch):
    def denied(*args, **kwargs):
        raise PermissionError("private OS diagnostics")

    monkeypatch.setattr(Path, "open", denied)
    with pytest.raises(ProjectSealError, match="permissions"):
        hash_file(artifact)


def test_symlink_output_rejected(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "is_symlink", lambda _: True)
    with pytest.raises(ProjectSealError, match="symbolic link"):
        check_output(tmp_path / "link", force=True)


def test_cancelled_sign_json(artifact, monkeypatch):
    def cancelled(*args, **kwargs):
        raise Cancelled()

    monkeypatch.setattr("projectseal.commands.sign.sign_release", cancelled)
    result = CliRunner().invoke(app, ["sign", str(artifact), "--json"])
    assert result.exit_code == 130
    assert '"CANCELLED"' in result.stdout


def test_invalid_author_website_json(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["init", "--website", "file:///secret", "--json"])
    assert result.exit_code == 1
    assert '"CONFIG_ERROR"' in result.stdout
    assert "file:///secret" not in result.stdout
