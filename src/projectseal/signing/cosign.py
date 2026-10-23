"""Narrow, fail-closed adapter for the pinned Cosign release."""

import re
import shutil
from pathlib import Path

from projectseal.config import TrustPolicy
from projectseal.exceptions import ProjectSealError, ToolError
from projectseal.utils.files import read_json, regular_file
from projectseal.utils.subprocess import run

SUPPORTED_VERSION = "3.1.4"
INSTALL_HELP = (
    "Install Cosign 3.1.4 from https://github.com/sigstore/cosign/releases/tag/v3.1.4 "
    "(Windows: cosign-windows-amd64.exe; macOS: cosign-darwin-amd64 or arm64; "
    "Linux: cosign-linux-amd64 or arm64), verify the download, rename to cosign "
    "(cosign.exe on Windows), and add its directory to PATH. "
    "See https://docs.sigstore.dev/cosign/system_config/installation/."
)


class Cosign:
    def __init__(self) -> None:
        executable = shutil.which("cosign")
        if not executable:
            raise ToolError("Cosign was not found. " + INSTALL_HELP)
        self.executable = executable
        result = run([executable, "version"], timeout=15)
        match = re.search(r"GitVersion:\s+v?(\d+\.\d+\.\d+)(\S*)", result.stdout)
        if result.returncode or not match or match[1] != SUPPORTED_VERSION or match[2]:
            raise ToolError("Unsupported or unreadable Cosign version. " + INSTALL_HELP)
        for command, flags in (
            (
                "sign-blob",
                ("--bundle", "--yes", "--key", "--fulcio-auth-flow"),
            ),
            (
                "verify-blob",
                ("--bundle", "--certificate-identity", "--certificate-oidc-issuer", "--key"),
            ),
        ):
            help_result = run([executable, command, "--help"], timeout=15)
            if help_result.returncode or any(
                re.search(rf"(?:^|\s){re.escape(flag)}(?=[\s=])", help_result.stdout) is None
                for flag in flags
            ):
                raise ToolError("Cosign does not expose the required bundle/identity options.")

    @staticmethod
    def modern_bundle(path: Path) -> bool:
        """Fail closed on legacy bundles, independently of the upstream security fix."""
        try:
            data = read_json(path, limit=16 * 1024 * 1024)
        except ProjectSealError:
            return False
        return (
            isinstance(data, dict)
            and isinstance(data.get("mediaType"), str)
            and data.get("mediaType")
            in {
                "application/vnd.dev.sigstore.bundle.v0.3+json",
                "application/vnd.dev.sigstore.bundle+json;version=0.3",
            }
            and isinstance(data.get("messageSignature"), dict)
            and bool(data["messageSignature"])
            and isinstance(data.get("verificationMaterial"), dict)
            and bool(data["verificationMaterial"])
        )

    def sign(
        self,
        artifact: Path,
        bundle: Path,
        *,
        key: Path | None = None,
        non_interactive: bool = False,
    ) -> None:
        args = [self.executable, "sign-blob", "--bundle", str(bundle.resolve())]
        if key is not None:
            args.extend(["--key", str(regular_file(key))])
        if non_interactive:
            args.append("--yes")
            if key is None:
                # Token flow cannot open the interactive browser/device login path.
                args.extend(["--fulcio-auth-flow", "token"])
        args.append(str(regular_file(artifact)))
        result = run(args, timeout=600, interactive=not non_interactive)
        if result.returncode:
            raise ProjectSealError(
                "Cosign signing failed. Check authentication, key access and network; "
                "retry directly with cosign for diagnostics. No new bundle was published.",
                "SIGNING_FAILED",
            )
        # A zero exit without a modern bundle is never a successful signing result.
        if not self.modern_bundle(bundle):
            raise ToolError("Cosign did not create a modern Sigstore bundle; reinstall Cosign.")

    def verify(
        self,
        artifact: Path,
        bundle: Path,
        *,
        policy: TrustPolicy | None = None,
        key: Path | None = None,
    ) -> bool:
        if (policy is None) == (key is None):
            raise ToolError("Verification requires exactly one explicit trust source.")
        if not self.modern_bundle(bundle):
            return False
        args = [self.executable, "verify-blob", "--bundle", str(regular_file(bundle))]
        if policy:
            args.extend(
                [
                    "--certificate-identity",
                    policy.certificate_identity,
                    "--certificate-oidc-issuer",
                    policy.certificate_oidc_issuer,
                ]
            )
        if key is not None:
            args.extend(["--key", str(regular_file(key))])
        args.append(str(regular_file(artifact)))
        result = run(args, timeout=180)
        # Cosign has no stable, structured failure taxonomy. Never parse stderr heuristically.
        return result.returncode == 0
