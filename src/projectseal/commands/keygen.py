from pathlib import Path

import typer

from projectseal.core.keys import generate_key_pair
from projectseal.utils.output import execute


def command(
    output_prefix: Path = typer.Option(
        ..., help="Local path prefix for .key/.pub files; use a private directory outside Git."
    ),
    non_interactive: bool = typer.Option(
        False, "--non-interactive", help="Require a nonempty COSIGN_PASSWORD; never prompt."
    ),
    json_mode: bool = typer.Option(False, "--json", help="JSON only; implies non-interactive."),
    no_color: bool = typer.Option(False, "--no-color", help="Disable terminal colors."),
) -> None:
    """Generate a local Cosign key pair without overwriting existing keys."""
    execute(
        lambda: generate_key_pair(output_prefix, non_interactive=non_interactive or json_mode),
        json_mode,
        no_color,
    )
