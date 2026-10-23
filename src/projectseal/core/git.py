import re
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from projectseal.exceptions import ToolError
from projectseal.utils.subprocess import run


@dataclass(frozen=True)
class GitInfo:
    available: bool = False
    branch: str | None = None
    commit: str | None = None
    dirty: bool | None = None
    repository: str | None = None

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def safe_remote(value: str) -> str | None:
    """Never persist credentials, query strings, or local filesystem remotes."""
    value = value.strip()
    if value.startswith(("https://", "http://", "ssh://", "git://")):
        parsed = urlsplit(value)
        if not parsed.hostname:
            return None
        return urlunsplit((parsed.scheme, parsed.hostname, parsed.path, "", ""))
    match = re.fullmatch(r"[^@\s]+@([\w.-]+):([\w./-]+)", value)
    if match:
        return f"ssh://{match[1]}/{match[2]}"
    return None


def inspect_git(root: Path) -> GitInfo:
    executable = shutil.which("git")
    if not executable:
        return GitInfo()

    def query(*args: str) -> str | None:
        result = run([executable, "-C", str(root.resolve()), *args], timeout=15)
        return result.stdout.strip() if result.returncode == 0 else None

    try:
        if query("rev-parse", "--is-inside-work-tree") != "true":
            return GitInfo()
        changes = query("status", "--porcelain")
        remote = query("remote", "get-url", "origin")
        return GitInfo(
            available=True,
            branch=query("symbolic-ref", "--short", "HEAD"),
            commit=query("rev-parse", "--verify", "HEAD"),
            dirty=bool(changes) if changes is not None else None,
            repository=safe_remote(remote) if remote else None,
        )
    except ToolError:
        # A missing/non-working optional Git executable does not block non-Git projects.
        return GitInfo()
