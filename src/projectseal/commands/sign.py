from pathlib import Path

import typer

from projectseal.core.release import sign_release
from projectseal.utils.output import execute


def command(
    file: Path = typer.Argument(..., help="Release artifact; keyless signing is the default."),
    output: Path | None = typer.Option(None, "--output", "-o", help="Custom Sigstore bundle path."),
    release_version: str | None = typer.Option(
        None, help="Also create and separately sign a manifest."
    ),
    key: Path | None = typer.Option(
        None, help="Optional LOCAL private key; keep outside the repository."
    ),
    non_interactive: bool = typer.Option(
        False, "--non-interactive", help="Accept log consent; use ambient OIDC or key credentials."
    ),
    force: bool = typer.Option(
        False, "--force", help="Explicitly replace existing release outputs."
    ),
    json_mode: bool = typer.Option(
        False, "--json", help="JSON only; implies non-interactive signing."
    ),
    no_color: bool = typer.Option(False, "--no-color", help="Disable terminal colors."),
) -> None:
    """Sign a stable artifact via Cosign. Keyless signing uses public Sigstore services/logs."""
    execute(
        lambda: sign_release(
            file,
            output=output,
            root=Path.cwd(),
            release_version=release_version,
            key=key,
            non_interactive=non_interactive or json_mode,
            force=force,
        ),
        json_mode,
        no_color,
    )
