from pathlib import Path

import typer

from projectseal.config import TrustPolicy, load_policy
from projectseal.core.verification import VerificationStatus, verify_release
from projectseal.exceptions import ProjectSealError
from projectseal.utils.output import emit, execute


def command(
    file: Path = typer.Argument(
        ..., help="Artifact to verify against independently established trust."
    ),
    bundle: Path | None = typer.Option(None, help="Defaults to FILE.sigstore.json."),
    certificate_identity: str | None = typer.Option(
        None, help="Exact expected signer identity; no regex."
    ),
    certificate_oidc_issuer: str | None = typer.Option(
        None, help="Exact expected HTTPS OIDC issuer."
    ),
    policy: Path | None = typer.Option(
        None, help="Explicitly trusted JSON policy; never auto-loaded."
    ),
    key: Path | None = typer.Option(None, help="Explicitly trusted LOCAL public key."),
    manifest: Path | None = typer.Option(
        None, help="Also authenticate and check this release manifest."
    ),
    manifest_bundle: Path | None = typer.Option(None, help="Defaults to MANIFEST.sigstore.json."),
    json_mode: bool = typer.Option(
        False, "--json", help="Emit one JSON result including failures."
    ),
    no_color: bool = typer.Option(False, "--no-color", help="Disable terminal colors."),
) -> None:
    """Verify signature AND expected trust. Unconstrained signatures never produce VALID."""

    def action() -> dict[str, object]:
        inline = certificate_identity is not None or certificate_oidc_issuer is not None
        if sum((inline, policy is not None, key is not None)) > 1:
            raise ProjectSealError("Choose identity flags, --policy, or --key.", "ARGUMENT_ERROR")
        if inline and (not certificate_identity or not certificate_oidc_issuer):
            raise ProjectSealError("Both exact identity and OIDC issuer are required.", "UNTRUSTED")
        trusted = (
            load_policy(policy)
            if policy is not None
            else (
                TrustPolicy(
                    certificate_identity=certificate_identity,
                    certificate_oidc_issuer=certificate_oidc_issuer,
                )
                if certificate_identity and certificate_oidc_issuer
                else None
            )
        )
        outcome = verify_release(
            file,
            bundle=bundle,
            policy=trusted,
            key=key,
            manifest=manifest,
            manifest_bundle=manifest_bundle,
        )
        data = outcome.model_dump(mode="json")
        if outcome.status != VerificationStatus.VALID:
            emit(data, json_mode, no_color)
            raise typer.Exit(1)
        return data

    execute(action, json_mode, no_color)
