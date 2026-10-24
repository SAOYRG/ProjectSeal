import json
import os
from pathlib import Path

import pytest
from typer.testing import CliRunner

from projectseal.cli import app
from projectseal.core.keys import generate_key_pair
from projectseal.exceptions import ProjectSealError
from projectseal.utils.files import atomic_write

PRIVATE = b"-----BEGIN ENCRYPTED SIGSTORE PRIVATE KEY-----\nprivate-stub\n"
PUBLIC = b"-----BEGIN PUBLIC KEY-----\npublic-stub\n"


@pytest.fixture
def key_backend(monkeypatch):
    state = {"calls": 0, "bad": False, "fail": False}

    class Backend:
        def generate_key_pair(self, prefix, **kwargs):
            state["calls"] += 1
            Path(str(prefix) + ".key").write_bytes(PRIVATE)
            if state["fail"]:
                raise ProjectSealError("failed", "KEY_GENERATION_FAILED")
            Path(str(prefix) + ".pub").write_bytes(b"invalid" if state["bad"] else PUBLIC)

    monkeypatch.setattr("projectseal.core.keys.Cosign", Backend)
    monkeypatch.setenv("COSIGN_PASSWORD", "test-password")
    return state


def test_generated_key_permissions_and_json(tmp_path, key_backend):
    prefix = tmp_path / "custom key & name"
    outcome = CliRunner().invoke(app, ["keygen", "--output-prefix", str(prefix), "--json"])
    assert outcome.exit_code == 0, outcome.output
    result = json.loads(outcome.stdout)
    assert result["status"] == "KEY_PAIR_CREATED"
    assert result["identity_verified"] is False
    assert Path(result["private_key"]).read_bytes() == PRIVATE
    assert len(result["public_key_file_sha256"]) == 64
    assert "private-stub" not in outcome.output
    assert "test-password" not in outcome.output
    assert not list(tmp_path.glob(".projectseal-key-*"))
    if os.name != "nt":
        assert Path(result["private_key"]).stat().st_mode & 0o777 == 0o600


@pytest.mark.parametrize("suffix", [".key", ".pub"])
def test_key_generation_never_overwrites(tmp_path, key_backend, suffix):
    existing = tmp_path / ("key" + suffix)
    existing.write_bytes(b"existing")
    with pytest.raises(ProjectSealError, match="Output exists"):
        generate_key_pair(tmp_path / "key", non_interactive=True)
    assert existing.read_bytes() == b"existing"
    assert key_backend["calls"] == 0


@pytest.mark.parametrize("password", [None, ""])
def test_json_requires_nonempty_password(tmp_path, monkeypatch, key_backend, password):
    if password is None:
        monkeypatch.delenv("COSIGN_PASSWORD")
    else:
        monkeypatch.setenv("COSIGN_PASSWORD", password)
    outcome = CliRunner().invoke(
        app, ["keygen", "--output-prefix", str(tmp_path / "key"), "--json"]
    )
    assert outcome.exit_code == 1
    assert json.loads(outcome.stdout)["status"] == "PASSWORD_REQUIRED"
    assert key_backend["calls"] == 0
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("failure", ["bad", "fail"])
def test_generation_failure_cleans_staged_private_key(tmp_path, key_backend, failure):
    key_backend[failure] = True
    with pytest.raises(ProjectSealError):
        generate_key_pair(tmp_path / "key", non_interactive=True)
    assert not list(tmp_path.iterdir())


def test_second_output_failure_rolls_back_private_key(tmp_path, monkeypatch, key_backend):
    def fail_public(path, data, force=False):
        if path.suffix == ".pub":
            raise ProjectSealError("injected disk failure")
        atomic_write(path, data, force)

    monkeypatch.setattr("projectseal.utils.files.atomic_write", fail_public)
    with pytest.raises(ProjectSealError, match="injected"):
        generate_key_pair(tmp_path / "key", non_interactive=True)
    assert not list(tmp_path.iterdir())


def test_backend_arguments_and_failure_redaction(tmp_path, monkeypatch):
    from projectseal.signing.cosign import Cosign
    from projectseal.utils.subprocess import ProcessResult

    calls = []

    def fake(args, **kwargs):
        calls.append((args, kwargs))
        return ProcessResult(1, "password-and-private-key")

    backend = object.__new__(Cosign)
    backend.executable = "cosign"
    monkeypatch.setattr("projectseal.signing.cosign.run", fake)
    with pytest.raises(ProjectSealError, match="key generation failed") as error:
        backend.generate_key_pair(tmp_path / "name & chars", non_interactive=True)
    assert "password-and-private-key" not in str(error.value)
    assert calls[0][0] == [
        "cosign",
        "generate-key-pair",
        "--output-key-prefix",
        str(tmp_path / "name & chars"),
    ]
    assert calls[0][1]["interactive"] is False


def test_empty_password_rejected_in_interactive_mode(tmp_path, monkeypatch, key_backend):
    monkeypatch.setenv("COSIGN_PASSWORD", "")
    with pytest.raises(ProjectSealError, match="nonempty"):
        generate_key_pair(tmp_path / "key")
    assert key_backend["calls"] == 0
