class ProjectSealError(Exception):
    """A safe, user-facing error; never includes external tool output."""

    def __init__(self, message: str, code: str = "ERROR") -> None:
        super().__init__(message)
        self.code = code


class ToolError(ProjectSealError):
    def __init__(self, message: str) -> None:
        super().__init__(message, "TOOL_ERROR")


class Cancelled(ProjectSealError):
    def __init__(self) -> None:
        super().__init__("Operation cancelled; no new signature was published.", "CANCELLED")
