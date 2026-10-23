from pathlib import Path

import typer

from projectseal.config import config_path
from projectseal.core.identity import initialize
from projectseal.exceptions import ProjectSealError
from projectseal.utils.output import execute


def command(
    name: str | None = typer.Option(None, help="Project display name."),
    author: str | None = typer.Option(None, help="Self-declared developer display name."),
    website: str | None = typer.Option(None, help="HTTP(S) project/developer homepage."),
    non_interactive: bool = typer.Option(
        False, "--non-interactive", help="Use defaults; never prompt."
    ),
    json_mode: bool = typer.Option(False, "--json", help="Emit only JSON; implies no prompts."),
    no_color: bool = typer.Option(False, "--no-color", help="Disable terminal colors."),
) -> None:
    """Create a local UUID and self-declared project identity without overwriting an identity."""

    def action() -> dict[str, object]:
        root = Path.cwd()
        if config_path(root).exists():
            raise ProjectSealError(
                "Already initialized; existing identity was preserved.", "ALREADY_EXISTS"
            )
        project_name, display_name, homepage = name, author, website
        if not non_interactive and not json_mode:
            project_name = name or typer.prompt("Project name", default=root.name)
            display_name = author or typer.prompt(
                "Developer display name (self-declared)", default="Developer"
            )
            homepage = website or typer.prompt(
                "Homepage (optional)", default="", show_default=False
            )
        project = initialize(root, project_name, display_name or "Developer", homepage or None)
        return {
            "status": "INITIALIZED",
            "project": project.model_dump(mode="json"),
            "message": "Display name is self-declared, not an authenticated identity.",
        }

    execute(action, json_mode, no_color)
