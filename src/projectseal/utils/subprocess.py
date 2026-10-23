"""Argument-array subprocess boundary. Child diagnostics are deliberately never logged."""

import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from projectseal.exceptions import Cancelled, ToolError


@dataclass(frozen=True)
class ProcessResult:
    returncode: int
    stdout: str


def run(
    args: Sequence[str], *, cwd: Path | None = None, timeout: int = 60, interactive: bool = False
) -> ProcessResult:
    try:
        result = subprocess.run(
            list(args),
            cwd=cwd,
            timeout=timeout,
            check=False,
            shell=False,
            stdin=None if interactive else subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            # Interactive Cosign needs its browser/device instructions. Only stderr is inherited.
            stderr=None if interactive else subprocess.PIPE,
            encoding="utf-8",
            errors="replace",
        )
    except KeyboardInterrupt as exc:
        raise Cancelled() from exc
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ToolError(
            "External tool could not run or timed out; check installation and network."
        ) from exc
    if result.returncode in {130, -2, 0xC000013A, -1073741510}:
        raise Cancelled()
    return ProcessResult(result.returncode, result.stdout)
