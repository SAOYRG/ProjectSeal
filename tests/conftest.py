import json
from pathlib import Path

import pytest

from projectseal.config import TrustPolicy
from projectseal.exceptions import ProjectSealError


@pytest.fixture
def artifact(tmp_path: Path) -> Path:
    path = tmp_path / "release 文件.bin"
    path.write_bytes(b"release\x00\xff\n")
    return path


@pytest.fixture
def policy() -> TrustPolicy:
    return TrustPolicy(
        certificate_identity="dev@example.com",
        certificate_oidc_issuer="https://accounts.google.com",
    )


class StubBackend:
    """Behavioral stub only; explicitly NOT cryptographic evidence."""

    def __init__(self, valid: bool = True, fail_sign: int = 0) -> None:
        self.valid = valid
        self.fail_sign = fail_sign
        self.sign_calls = 0
        self.verify_calls = 0

    def sign(self, artifact: Path, bundle: Path, **kwargs: object) -> None:
        self.sign_calls += 1
        if self.sign_calls == self.fail_sign:
            raise ProjectSealError("stub signing failed", "SIGNING_FAILED")
        bundle.write_text(json.dumps({"stub": True}), encoding="utf-8")

    def verify(self, artifact: Path, bundle: Path, **kwargs: object) -> bool:
        self.verify_calls += 1
        return self.valid


@pytest.fixture
def stub() -> StubBackend:
    return StubBackend()
