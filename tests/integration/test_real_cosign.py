"""Opt-in live tests. They never authenticate unless PROJECTSEAL_KEYLESS_TEST=1."""

import os
from pathlib import Path

import pytest

from projectseal.config import TrustPolicy
from projectseal.core.identity import initialize
from projectseal.core.release import default_manifest, sign_release
from projectseal.core.verification import VerificationStatus, verify_release


@pytest.mark.cosign
def test_public_release_bundle(tmp_path):
    artifact = os.environ.get("PROJECTSEAL_TEST_ARTIFACT")
    bundle = os.environ.get("PROJECTSEAL_TEST_BUNDLE")
    identity = os.environ.get("PROJECTSEAL_TEST_IDENTITY")
    issuer = os.environ.get("PROJECTSEAL_TEST_ISSUER")
    if not all((artifact, bundle, identity, issuer)):
        pytest.skip(
            "Set PROJECTSEAL_TEST_ARTIFACT/BUNDLE/IDENTITY/ISSUER to trusted fixture inputs"
        )
    file = Path(artifact)
    evidence = Path(bundle)
    policy = TrustPolicy(certificate_identity=identity, certificate_oidc_issuer=issuer)
    assert verify_release(file, bundle=evidence, policy=policy).status == VerificationStatus.VALID
    changed = tmp_path / "modified.bin"
    changed.write_bytes(file.read_bytes() + b"tampered")
    assert (
        verify_release(changed, bundle=evidence, policy=policy).status
        == VerificationStatus.VERIFICATION_FAILED
    )
    wrong_identity = policy.model_copy(update={"certificate_identity": "untrusted@example.invalid"})
    assert (
        verify_release(file, bundle=evidence, policy=wrong_identity).status
        == VerificationStatus.VERIFICATION_FAILED
    )
    wrong_issuer = policy.model_copy(
        update={"certificate_oidc_issuer": "https://issuer.example.invalid"}
    )
    assert (
        verify_release(file, bundle=evidence, policy=wrong_issuer).status
        == VerificationStatus.VERIFICATION_FAILED
    )


@pytest.mark.cosign
@pytest.mark.keyless
def test_live_keyless_sign_and_verify(tmp_path):
    if os.environ.get("PROJECTSEAL_KEYLESS_TEST") != "1":
        pytest.skip(
            "Explicit opt-in required: PROJECTSEAL_KEYLESS_TEST=1 and expected identity/issuer"
        )
    policy = TrustPolicy(
        certificate_identity=os.environ["PROJECTSEAL_TEST_IDENTITY"],
        certificate_oidc_issuer=os.environ["PROJECTSEAL_TEST_ISSUER"],
    )
    file = tmp_path / "release.txt"
    file.write_text("ProjectSeal live keyless integration test\n", encoding="utf-8")
    initialize(tmp_path)
    sign_release(file, root=tmp_path, release_version="0.1.0", non_interactive=True)
    result = verify_release(file, policy=policy, manifest=default_manifest(file))
    assert result.status == VerificationStatus.VALID
    assert result.manifest_authenticated
    wrong = policy.model_copy(update={"certificate_identity": "untrusted@example.invalid"})
    assert verify_release(file, policy=wrong).status == VerificationStatus.VERIFICATION_FAILED
    file.write_text("tampered", encoding="utf-8")
    assert verify_release(file, policy=policy).status == VerificationStatus.VERIFICATION_FAILED
    assert (
        verify_release(file, policy=policy, manifest=default_manifest(file)).status
        == VerificationStatus.FILE_MODIFIED
    )


@pytest.mark.cosign
def test_live_key_sign_and_verify(tmp_path):
    private = os.environ.get("PROJECTSEAL_TEST_PRIVATE_KEY")
    public = os.environ.get("PROJECTSEAL_TEST_PUBLIC_KEY")
    if not private or not public:
        pytest.skip("Set PROJECTSEAL_TEST_PRIVATE_KEY/PUBLIC_KEY to disposable Cosign key files")
    file = tmp_path / "release.txt"
    file.write_text("ProjectSeal disposable key integration test\n", encoding="utf-8")
    initialize(tmp_path)
    sign_release(
        file, key=Path(private), root=tmp_path, release_version="0.1.0", non_interactive=True
    )
    result = verify_release(file, key=Path(public), manifest=default_manifest(file))
    assert result.status == VerificationStatus.VALID
    assert result.manifest_authenticated
    file.write_text("tampered", encoding="utf-8")
    assert verify_release(file, key=Path(public)).status == VerificationStatus.VERIFICATION_FAILED
    assert (
        verify_release(file, key=Path(public), manifest=default_manifest(file)).status
        == VerificationStatus.FILE_MODIFIED
    )
