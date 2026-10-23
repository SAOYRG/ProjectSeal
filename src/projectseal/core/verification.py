"""Verification never learns trust from an artifact, its bundle, or project.json."""

import shutil
import tempfile
from enum import StrEnum
from pathlib import Path

from pydantic import ValidationError

from projectseal.config import Model, TrustPolicy
from projectseal.core.hashing import hash_file
from projectseal.core.manifest import Manifest
from projectseal.core.release import default_bundle
from projectseal.exceptions import ProjectSealError
from projectseal.signing.base import SigningBackend
from projectseal.signing.cosign import Cosign
from projectseal.utils.files import read_json, regular_file


class VerificationStatus(StrEnum):
    VALID = "VALID"
    INVALID_SIGNATURE = "INVALID_SIGNATURE"
    IDENTITY_MISMATCH = "IDENTITY_MISMATCH"
    FILE_MODIFIED = "FILE_MODIFIED"
    MISSING_BUNDLE = "MISSING_BUNDLE"
    UNTRUSTED = "UNTRUSTED"
    TOOL_ERROR = "TOOL_ERROR"
    VERIFICATION_FAILED = "VERIFICATION_FAILED"
    INVALID_MANIFEST = "INVALID_MANIFEST"


class VerificationResult(Model):
    status: VerificationStatus
    file: str
    message: str
    certificate_identity: str | None = None
    certificate_oidc_issuer: str | None = None
    trust_source: str | None = None
    manifest_authenticated: bool = False
    manifest: Manifest | None = None


def verify_release(
    artifact: Path,
    *,
    bundle: Path | None = None,
    policy: TrustPolicy | None = None,
    key: Path | None = None,
    manifest: Path | None = None,
    manifest_bundle: Path | None = None,
    backend: SigningBackend | None = None,
) -> VerificationResult:
    def result(status: VerificationStatus, message: str) -> VerificationResult:
        return VerificationResult(status=status, file=str(artifact), message=message)

    regular_file(artifact)
    evidence = bundle or default_bundle(artifact)
    if not evidence.is_file():
        return result(VerificationStatus.MISSING_BUNDLE, "Bundle missing; supply --bundle PATH.")
    if (policy is None) == (key is None):
        return result(
            VerificationStatus.UNTRUSTED,
            "Provide exact --certificate-identity and --certificate-oidc-issuer, "
            "an independently trusted --policy, or a trusted --key public key.",
        )
    if manifest_bundle is not None and manifest is None:
        raise ProjectSealError("--manifest-bundle requires --manifest.", "ARGUMENT_ERROR")
    try:
        verifier = backend if backend is not None else Cosign()
        with tempfile.TemporaryDirectory(prefix="projectseal-verify-") as scratch:
            work = Path(scratch)
            snapshot = work / "artifact"
            signed_bundle = work / "bundle.json"
            shutil.copyfile(regular_file(artifact), snapshot)
            shutil.copyfile(regular_file(evidence), signed_bundle)
            before = hash_file(snapshot)
            authenticated: Manifest | None = None
            if manifest is not None:
                metadata = work / "manifest.json"
                metadata_bundle = work / "manifest.sigstore.json"
                metadata_evidence = manifest_bundle or default_bundle(manifest)
                if not metadata_evidence.is_file():
                    return result(VerificationStatus.MISSING_BUNDLE, "Manifest bundle is missing.")
                shutil.copyfile(regular_file(manifest), metadata)
                shutil.copyfile(regular_file(metadata_evidence), metadata_bundle)
                if not verifier.verify(metadata, metadata_bundle, policy=policy, key=key):
                    return result(
                        VerificationStatus.VERIFICATION_FAILED,
                        "Manifest signature/trust verification failed; no claims accepted.",
                    )
                try:
                    authenticated = Manifest.model_validate(read_json(metadata))
                    if metadata.read_bytes() != authenticated.canonical_bytes():
                        raise ValueError("noncanonical manifest")
                except (ValidationError, ValueError, ProjectSealError):
                    return result(
                        VerificationStatus.INVALID_MANIFEST,
                        "Authenticated manifest is malformed or not canonical 1.0 JSON.",
                    )
                if (authenticated.artifact.sha256, authenticated.artifact.size) != (
                    before.digest,
                    before.size,
                ):
                    return result(
                        VerificationStatus.FILE_MODIFIED,
                        "Artifact differs from the independently authenticated manifest.",
                    )
            if not verifier.verify(snapshot, signed_bundle, policy=policy, key=key):
                return result(
                    VerificationStatus.VERIFICATION_FAILED,
                    "Cosign rejected verification. Possible causes include signature/content, "
                    "identity/issuer, trust evidence or connectivity. No identity was accepted.",
                )
            current = hash_file(artifact)
            if (current.digest, current.size) != (before.digest, before.size):
                return result(
                    VerificationStatus.FILE_MODIFIED, "Artifact changed during verification."
                )
            return VerificationResult(
                status=VerificationStatus.VALID,
                file=str(artifact),
                message="Signature, artifact integrity and explicit trust verified by Cosign.",
                certificate_identity=policy.certificate_identity if policy else None,
                certificate_oidc_issuer=policy.certificate_oidc_issuer if policy else None,
                trust_source="certificate_identity" if policy else "public_key",
                manifest_authenticated=authenticated is not None,
                manifest=authenticated,
            )
    except ProjectSealError as exc:
        if exc.code == "TOOL_ERROR":
            return result(VerificationStatus.TOOL_ERROR, str(exc))
        raise
