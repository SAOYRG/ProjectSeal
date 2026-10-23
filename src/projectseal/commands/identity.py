from pathlib import Path

import typer

from projectseal.config import load_project
from projectseal.utils.output import execute


def command(
    json_mode: bool = typer.Option(False, "--json", help="Emit only JSON."),
    no_color: bool = typer.Option(False, "--no-color", help="Disable terminal colors."),
) -> None:
    """Show the local project's self-declared identity (not proof of authorship)."""
    execute(
        lambda: {
            "project": load_project(Path.cwd()).model_dump(mode="json"),
            "authenticated": False,
        },
        json_mode,
        no_color,
    )
