import json
import subprocess
from pathlib import Path

import pytest

from projectseal.exceptions import Cancelled, ProjectSealError, ToolError
from projectseal.signing.cosign import Cosign
from projectseal.utils.subprocess import ProcessResult, run


@pytest.fixture
def cosign_stub(monkeypatch):
    calls = []
    state = {"exit": 0, "version": "3.0.2", "write_bundle": True, "help": True}

    def fake_run(args, **kwargs):
        calls.append((args, kwargs))
        if args[1] == "version":
            return ProcessResult(0, f"GitVersion: v{state['version']}\n")
        if "--help" in args:
            return ProcessResult(
                0,
                "--bundle --yes --key --new-bundle-format --fulcio-auth-flow "
                "--certificate-identity --certificate-oidc-issuer "
                if state["help"]
                else "",
            )
        if args[1] == "sign-blob" and state["write_bundle"]:
            Path(args[args.index("--bundle") + 1]).write_text(
                json.dumps(
                    {
                        "mediaType": "application/vnd.dev.sigstore.bundle.v0.3+json",
                        "messageSignature": {"signature": "stub-only"},
                        "verificationMaterial": {"tlogEntries": ["stub-only"]},
                    }
                )
            )
        return ProcessResult(state["exit"], "SECRET_ID_TOKEN private password")

    monkeypatch.setattr("projectseal.signing.cosign.shutil.which", lambda _: "cosign")
    monkeypatch.setattr("projectseal.signing.cosign.run", fake_run)
    return state, calls


def test_missing_cosign(monkeypatch):
    monkeypatch.setattr("projectseal.signing.cosign.shutil.which", lambda _: None)
    with pytest.raises(ToolError, match="Install Cosign 3.0.2"):
        Cosign()


@pytest.mark.parametrize("version", ["2.6.0", "3.0.1", "3.0.3", "3.0.2-rc.1", "4.0.0", "garbage"])
def test_unvalidated_versions_rejected(cosign_stub, version):
    cosign_stub[0]["version"] = version
    with pytest.raises(ToolError, match="Unsupported"):
        Cosign()


def test_required_flags_checked(cosign_stub):
    cosign_stub[0]["help"] = False
    with pytest.raises(ToolError, match="required"):
        Cosign()


def test_sign_arguments_and_bundle(cosign_stub, artifact, tmp_path):
    backend = Cosign()
    bundle = tmp_path / "bundle.json"
    backend.sign(artifact, bundle, non_interactive=True)
    args, options = cosign_stub[1][-1]
    assert args[1] == "sign-blob"
    assert "--yes" in args
    assert args[args.index("--fulcio-auth-flow") + 1] == "token"
    assert args[-1] == str(artifact.resolve())
    assert not options["interactive"]
    assert bundle.exists()


def test_external_secrets_never_in_exception(cosign_stub, artifact, tmp_path):
    backend = Cosign()
    cosign_stub[0]["exit"] = 1
    with pytest.raises(ProjectSealError) as error:
        backend.sign(artifact, tmp_path / "bundle", non_interactive=True)
    assert "SECRET" not in str(error.value)
    assert "password" not in str(error.value)


def test_zero_exit_without_bundle_is_error(cosign_stub, artifact, tmp_path):
    backend = Cosign()
    cosign_stub[0]["write_bundle"] = False
    with pytest.raises(ToolError, match="modern Sigstore bundle"):
        backend.sign(artifact, tmp_path / "missing", non_interactive=True)


def test_verification_exact_identity_no_bypasses(cosign_stub, artifact, tmp_path, policy):
    bundle = tmp_path / "bundle"
    bundle.write_text("{}")
    assert Cosign().verify(artifact, bundle, policy=policy)
    args, options = cosign_stub[1][-1]
    assert args[args.index("--certificate-identity") + 1] == policy.certificate_identity
    assert args[args.index("--certificate-oidc-issuer") + 1] == policy.certificate_oidc_issuer
    assert not any("regexp" in arg or "insecure" in arg for arg in args)
    assert not options.get("interactive", False)


def test_public_key_options(cosign_stub, artifact, tmp_path):
    key = tmp_path / "trusted.pub"
    key.write_bytes(b"test key")
    bundle = tmp_path / "bundle"
    backend = Cosign()
    backend.sign(artifact, bundle, key=key, non_interactive=True)
    assert "--key" in cosign_stub[1][-1][0]
    assert backend.verify(artifact, bundle, key=key)
    assert "--certificate-identity" not in cosign_stub[1][-1][0]


@pytest.mark.parametrize(
    "failure", [KeyboardInterrupt(), OSError("secret"), subprocess.TimeoutExpired("secret", 1)]
)
def test_process_failure_redaction(monkeypatch, failure):
    def broken(*args, **kwargs):
        raise failure

    monkeypatch.setattr("projectseal.utils.subprocess.subprocess.run", broken)
    with pytest.raises((ToolError, Cancelled)) as error:
        run(["cosign", "SECRET"])
    assert "secret" not in str(error.value).lower()


@pytest.mark.parametrize("code", [130, -2, -1073741510])
def test_user_cancellation_exit(monkeypatch, code):
    monkeypatch.setattr(
        "projectseal.utils.subprocess.subprocess.run",
        lambda *a, **kw: subprocess.CompletedProcess(a, code, stdout="", stderr=""),
    )
    with pytest.raises(Cancelled):
        run(["cosign", "sign-blob"])


def test_subprocess_never_uses_shell(monkeypatch):
    recorded = {}

    def fake(args, **kwargs):
        recorded.update(kwargs)
        assert args == ["cosign", "file & $(echo bad)"]
        return subprocess.CompletedProcess(args, 0, stdout="ok", stderr="secret")

    monkeypatch.setattr("projectseal.utils.subprocess.subprocess.run", fake)
    assert run(["cosign", "file & $(echo bad)"]).stdout == "ok"
    assert recorded["shell"] is False
