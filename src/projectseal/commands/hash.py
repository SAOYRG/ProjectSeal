from pathlib import Path

import typer

from projectseal.core.hashing import hash_file
from projectseal.utils.output import execute


def command(
    file: Path = typer.Argument(..., help="Regular file to hash using streaming SHA-256."),
    json_mode: bool = typer.Option(False, "--json", help="Emit only JSON."),
    no_color: bool = typer.Option(False, "--no-color", help="Disable terminal colors."),
) -> None:
    """Compute content integrity information; a hash does not authenticate an author."""
    execute(lambda: hash_file(file).model_dump(mode="json"), json_mode, no_color)
