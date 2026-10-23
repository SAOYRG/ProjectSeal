import json
import subprocess

import pytest
from typer.testing import CliRunner

from projectseal.cli import app
from projectseal.core.release import default_bundle

runner = CliRunner()


@pytest.mark.parametrize(
    "command", [[], ["init"], ["status"], ["identity"], ["hash"], ["sign"], ["verify"]]
)
def test_help(command):
    result = runner.invoke(app, [*command, "--help"])
    assert result.exit_code == 0
    assert "Usage:" in result.stdout


def test_version():
    assert "0.1.0" in runner.invoke(app, ["--version"]).stdout


def test_init_identity_status_hash(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init", "--non-interactive", "--name", "中文 App", "--json"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout)["project"]["project_name"] == "中文 App"
    assert json.loads(runner.invoke(app, ["identity", "--json"]).stdout)["authenticated"] is False
    status = runner.invoke(app, ["status", "--json"])
    assert json.loads(status.stdout)["initialized"] is True
    artifact = tmp_path / "data & chars.bin"
    artifact.write_bytes(b"abc")
    hashed = runner.invoke(app, ["hash", str(artifact), "--json"])
    assert (
        json.loads(hashed.stdout)["digest"]
        == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    )
    duplicate = runner.invoke(app, ["init", "--json"])
    assert duplicate.exit_code == 1
    assert json.loads(duplicate.stdout)["status"] == "ALREADY_EXISTS"


def test_interactive_init(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init"], input="Application\nDeveloper\nhttps://example.com\n")
    assert result.exit_code == 0
    assert "INITIALIZED" in result.stdout


def test_noninitialized_status_and_identity(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert json.loads(runner.invoke(app, ["status", "--json"]).stdout)["initialized"] is False
    outcome = runner.invoke(app, ["identity", "--json"])
    assert outcome.exit_code == 1
    assert json.loads(outcome.stdout)["status"] == "NOT_INITIALIZED"


def test_missing_artifact_json(tmp_path):
    for command in ("hash", "sign", "verify"):
        outcome = runner.invoke(app, [command, str(tmp_path / "missing"), "--json"])
        assert outcome.exit_code == 1
        assert json.loads(outcome.stdout)["status"] == "FILE_ERROR"


def test_no_implicit_trust_from_project_or_bundle(artifact, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init", "--json"])
    default_bundle(artifact).write_text('{"certificate_identity":"attacker@example.com"}')
    result = runner.invoke(app, ["verify", str(artifact), "--json"])
    assert result.exit_code == 1
    assert json.loads(result.stdout)["status"] == "UNTRUSTED"


@pytest.mark.parametrize(
    "args",
    [
        ["--certificate-identity", "dev@example.com"],
        ["--certificate-oidc-issuer", "https://accounts.google.com"],
        ["--policy", "trust.json", "--key", "public.pub"],
    ],
)
def test_invalid_trust_arguments(artifact, args):
    result = runner.invoke(app, ["verify", str(artifact), *args, "--json"])
    assert result.exit_code == 1
    assert json.loads(result.stdout)["status"] in {"UNTRUSTED", "ARGUMENT_ERROR"}


def test_cli_sign_verify_stub(artifact, stub, policy, monkeypatch):
    monkeypatch.setattr("projectseal.core.release.Cosign", lambda: stub)
    monkeypatch.setattr("projectseal.core.verification.Cosign", lambda: stub)
    signed = runner.invoke(app, ["sign", str(artifact), "--json"])
    assert signed.exit_code == 0, signed.output
    assert json.loads(signed.stdout)["identity_verified"] is False
    args = [
        "verify",
        str(artifact),
        "--certificate-identity",
        policy.certificate_identity,
        "--certificate-oidc-issuer",
        policy.certificate_oidc_issuer,
        "--json",
    ]
    assert json.loads(runner.invoke(app, args).stdout)["status"] == "VALID"
    stub.valid = False
    failed = runner.invoke(app, args)
    assert failed.exit_code == 1
    assert json.loads(failed.stdout)["status"] == "VERIFICATION_FAILED"


def test_missing_cosign_cli_redaction(artifact, monkeypatch):
    monkeypatch.setattr("projectseal.signing.cosign.shutil.which", lambda _: None)
    result = runner.invoke(app, ["sign", str(artifact), "--json"])
    assert result.exit_code == 1
    assert json.loads(result.stdout)["status"] == "TOOL_ERROR"


def test_real_git_integration(tmp_path):
    def git(*args):
        return subprocess.run(["git", "-C", str(tmp_path), *args], capture_output=True, check=True)

    git("init")
    git("config", "user.name", "Test")
    git("config", "user.email", "test@example.invalid")
    git("-c", "commit.gpgsign=false", "commit", "--allow-empty", "-m", "test")
    git("remote", "add", "origin", "https://user:secret@example.com/project.git?token=secret")
    from projectseal.core.git import inspect_git

    info = inspect_git(tmp_path)
    assert info.available
    assert len(info.commit) == 40
    assert info.dirty is False
    assert info.repository == "https://example.com/project.git"
    (tmp_path / "untracked.txt").write_text("change")
    assert inspect_git(tmp_path).dirty is True
