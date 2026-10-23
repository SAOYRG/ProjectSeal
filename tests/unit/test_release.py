import json
from pathlib import Path

import pytest

from projectseal.config import config_path
from projectseal.core.identity import initialize
from projectseal.core.release import default_bundle, default_manifest, sign_release
from projectseal.core.verification import VerificationStatus as Status
from projectseal.core.verification import verify_release
from projectseal.exceptions import ProjectSealError, ToolError
from projectseal.utils.files import canonical_json


def test_sign_and_verify_manifest(artifact, tmp_path, stub, policy):
    initialize(tmp_path)
    outcome = sign_release(artifact, root=tmp_path, release_version="1.2.3", backend=stub)
    assert outcome["status"] == "SIGNED"
    assert stub.sign_calls == 2
    verified = verify_release(
        artifact, manifest=default_manifest(artifact), policy=policy, backend=stub
    )
    assert verified.status == Status.VALID
    assert verified.manifest_authenticated
    assert verified.manifest.version == "1.2.3"


def test_sign_without_project(artifact, stub):
    sign_release(artifact, backend=stub)
    assert default_bundle(artifact).exists()


@pytest.mark.parametrize("target", ["artifact", "key", "config"])
def test_force_cannot_overwrite_inputs(artifact, tmp_path, stub, target):
    initialize(tmp_path)
    key = tmp_path / "private.key"
    key.write_bytes(b"do not overwrite")
    output = {"artifact": artifact, "key": key, "config": config_path(tmp_path)}[target]
    original = output.read_bytes()
    with pytest.raises(ProjectSealError, match="overwrite an input"):
        sign_release(artifact, output=output, root=tmp_path, key=key, force=True, backend=stub)
    assert output.read_bytes() == original
    assert stub.sign_calls == 0


def test_conflicting_manifest_output(artifact, tmp_path, stub):
    initialize(tmp_path)
    with pytest.raises(ProjectSealError, match="conflict"):
        sign_release(
            artifact,
            output=default_manifest(artifact),
            root=tmp_path,
            release_version="1.0",
            backend=stub,
        )


def test_hardlink_input_is_protected(artifact, tmp_path, stub):
    alias = tmp_path / "alias"
    try:
        alias.hardlink_to(artifact)
    except OSError:
        pytest.skip("Hard links unavailable in this sandbox/filesystem")
    with pytest.raises(ProjectSealError, match="overwrite an input"):
        sign_release(artifact, output=alias, force=True, backend=stub)


def test_existing_bundle_and_force(artifact, stub):
    path = default_bundle(artifact)
    path.write_bytes(b"previous")
    with pytest.raises(ProjectSealError, match="Output exists"):
        sign_release(artifact, backend=stub)
    assert path.read_bytes() == b"previous"
    sign_release(artifact, force=True, backend=stub)
    assert path.read_bytes() != b"previous"


def test_failed_second_signature_preserves_outputs(artifact, tmp_path, stub):
    initialize(tmp_path)
    stub.fail_sign = 2
    previous = default_bundle(artifact)
    previous.write_bytes(b"original")
    with pytest.raises(ProjectSealError):
        sign_release(artifact, root=tmp_path, release_version="1.0", force=True, backend=stub)
    assert previous.read_bytes() == b"original"
    assert not default_manifest(artifact).exists()


def test_concurrent_artifact_modification_rejected(artifact, stub):
    original = stub.sign

    def changing(*args, **kwargs):
        original(*args, **kwargs)
        artifact.write_bytes(b"changed during auth")

    stub.sign = changing
    with pytest.raises(ProjectSealError, match="changed during signing"):
        sign_release(artifact, backend=stub)
    assert not default_bundle(artifact).exists()


@pytest.mark.parametrize(
    "with_policy,with_bundle,expected",
    [
        (False, True, Status.UNTRUSTED),
        (True, False, Status.MISSING_BUNDLE),
        (True, True, Status.VALID),
    ],
)
def test_trust_required(artifact, stub, policy, with_policy, with_bundle, expected):
    if with_bundle:
        default_bundle(artifact).write_text("{}")
    outcome = verify_release(artifact, policy=policy if with_policy else None, backend=stub)
    assert outcome.status == expected
    assert stub.verify_calls == (1 if expected == Status.VALID else 0)


@pytest.mark.parametrize(
    "scenario", ["tamper", "wrong_identity", "wrong_issuer", "invalid_signature"]
)
def test_failed_cosign_is_generic_not_guessed(artifact, stub, policy, scenario):
    default_bundle(artifact).write_text("{}")
    stub.valid = False
    outcome = verify_release(artifact, policy=policy, backend=stub)
    assert outcome.status == Status.VERIFICATION_FAILED
    assert outcome.certificate_identity is None
    assert not outcome.manifest_authenticated


def test_authenticated_manifest_detects_modification(artifact, tmp_path, stub, policy):
    initialize(tmp_path)
    sign_release(artifact, root=tmp_path, release_version="1.0", backend=stub)
    artifact.write_bytes(b"modified")
    outcome = verify_release(
        artifact, manifest=default_manifest(artifact), policy=policy, backend=stub
    )
    assert outcome.status == Status.FILE_MODIFIED
    assert stub.verify_calls == 1


def test_untrusted_manifest_claims_not_used(artifact, tmp_path, stub, policy):
    initialize(tmp_path)
    sign_release(artifact, root=tmp_path, release_version="1.0", backend=stub)
    stub.valid = False
    path = default_manifest(artifact)
    data = json.loads(path.read_bytes())
    data["artifact"]["sha256"] = "0" * 64
    path.write_bytes(canonical_json(data))
    result = verify_release(artifact, manifest=path, policy=policy, backend=stub)
    assert result.status == Status.VERIFICATION_FAILED
    assert result.manifest is None


@pytest.mark.parametrize("raw", [b"{}", b"bad JSON"])
def test_authenticated_invalid_manifest(artifact, raw, stub, policy):
    default_bundle(artifact).write_bytes(b"{}")
    path = default_manifest(artifact)
    path.write_bytes(raw)
    default_bundle(path).write_bytes(b"{}")
    outcome = verify_release(artifact, policy=policy, manifest=path, backend=stub)
    assert outcome.status == Status.INVALID_MANIFEST


def test_noncanonical_manifest_rejected(artifact, tmp_path, stub, policy):
    initialize(tmp_path)
    sign_release(artifact, root=tmp_path, release_version="1.0", backend=stub)
    path = default_manifest(artifact)
    path.write_bytes(path.read_bytes() + b"\n")
    assert (
        verify_release(artifact, policy=policy, manifest=path, backend=stub).status
        == Status.INVALID_MANIFEST
    )


def test_missing_manifest_evidence(artifact, stub, policy):
    default_bundle(artifact).write_text("{}")
    assert (
        verify_release(artifact, policy=policy, manifest=Path("missing.json"), backend=stub).status
        == Status.MISSING_BUNDLE
    )


def test_tool_error(artifact, monkeypatch, policy):
    default_bundle(artifact).write_text("{}")

    def broken():
        raise ToolError("tool unavailable")

    monkeypatch.setattr("projectseal.core.verification.Cosign", broken)
    assert verify_release(artifact, policy=policy).status == Status.TOOL_ERROR


def test_verification_checks_original_after_snapshot(artifact, stub, policy):
    default_bundle(artifact).write_text("{}")

    def changing(*args, **kwargs):
        artifact.write_bytes(b"changed")
        return True

    stub.verify = changing
    assert verify_release(artifact, policy=policy, backend=stub).status == Status.FILE_MODIFIED


def test_public_key_trust(artifact, tmp_path, stub):
    default_bundle(artifact).write_text("{}")
    key = tmp_path / "public.pub"
    key.write_bytes(b"not a real key; stub only")
    outcome = verify_release(artifact, key=key, backend=stub)
    assert outcome.status == Status.VALID
    assert outcome.trust_source == "public_key"
    assert outcome.certificate_identity is None
