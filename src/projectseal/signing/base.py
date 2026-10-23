from pathlib import Path
from typing import Protocol

from projectseal.config import TrustPolicy


class SigningBackend(Protocol):
    def sign(
        self,
        artifact: Path,
        bundle: Path,
        *,
        key: Path | None = None,
        non_interactive: bool = False,
    ) -> None: ...

    def verify(
        self,
        artifact: Path,
        bundle: Path,
        *,
        policy: TrustPolicy | None = None,
        key: Path | None = None,
    ) -> bool: ...
