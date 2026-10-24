"""Explicit local key generation, delegated to Cosign's cryptographic implementation."""

import hashlib
import os
import tempfile
from pathlib import Path
from typing import Any

from projectseal.exceptions import ProjectSealError, ToolError
from projectseal.signing.cosign import Cosign
from projectseal.utils.files import check_output, publish_files


def generate_key_pair(prefix: Path, *, non_interactive: bool = False) -> dict[str, Any]:
    private = prefix.parent / (prefix.name + ".key")
    public = prefix.parent / (prefix.name + ".pub")
    # Check before expensive generation, and again at atomic publication. No --force exists.
    for path in (private, public):
        check_output(path)
    if (non_interactive and not os.environ.get("COSIGN_PASSWORD")) or (
        "COSIGN_PASSWORD" in os.environ and not os.environ["COSIGN_PASSWORD"]
    ):
        raise ProjectSealError(
            "Set a nonempty COSIGN_PASSWORD through a secret store, or run interactively. "
            "Passwords must never be passed as command arguments.",
            "PASSWORD_REQUIRED",
        )
    backend = Cosign()
    # Python creates the staging directory with mode 0700 on POSIX. Windows inherits ACLs.
    with tempfile.TemporaryDirectory(dir=prefix.parent, prefix=".projectseal-key-") as temp:
        staged = Path(temp) / "key"
        backend.generate_key_pair(staged, non_interactive=non_interactive)
        private_data = Path(str(staged) + ".key").read_bytes()
        public_data = Path(str(staged) + ".pub").read_bytes()
        if not private_data.startswith(b"-----BEGIN ENCRYPTED SIGSTORE PRIVATE KEY-----") or (
            not public_data.startswith(b"-----BEGIN PUBLIC KEY-----")
        ):
            raise ToolError("Cosign did not create the expected encrypted key pair.")
        # Atomic writes use mode-0600 temporary files on POSIX; no private bytes are emitted.
        publish_files({private: private_data, public: public_data})
    return {
        "status": "KEY_PAIR_CREATED",
        "private_key": str(private.resolve()),
        "public_key": str(public.resolve()),
        "public_key_file_sha256": hashlib.sha256(public_data).hexdigest(),
        "identity_verified": False,
    }
