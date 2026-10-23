from pathlib import Path

import typer

from projectseal.core.status import project_status
from projectseal.utils.output import execute


def command(
    json_mode: bool = typer.Option(False, "--json", help="Emit only JSON."),
    no_color: bool = typer.Option(False, "--no-color", help="Disable terminal colors."),
) -> None:
    """Show initialization, Git state and nearby release manifests as untrusted references."""

    execute(lambda: project_status(Path.cwd()), json_mode, no_color)
