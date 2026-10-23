import json
from collections.abc import Callable
from typing import Any

import typer
from pydantic import ValidationError
from rich.console import Console

from projectseal.exceptions import ProjectSealError


def emit(data: dict[str, Any], json_mode: bool, no_color: bool = False) -> None:
    if json_mode:
        typer.echo(json.dumps(data, ensure_ascii=False, allow_nan=False))
        return
    console = Console(no_color=no_color, highlight=False, markup=False)
    for key, value in data.items():
        if value is not None:
            display = (
                json.dumps(value, ensure_ascii=False)
                if isinstance(value, (dict, list))
                else str(value)
            )
            console.print(f"{key.replace('_', ' ').title()}: {display}")


def execute(action: Callable[[], dict[str, Any]], json_mode: bool, no_color: bool = False) -> None:
    try:
        emit(action(), json_mode, no_color)
    except (ProjectSealError, ValidationError, OSError, KeyboardInterrupt) as exc:
        if isinstance(exc, ProjectSealError):
            code, message = exc.code, str(exc)
        elif isinstance(exc, ValidationError):
            code, message = (
                "CONFIG_ERROR",
                "Invalid input fields; check names, URL and schema types.",
            )
        elif isinstance(exc, KeyboardInterrupt):
            code, message = "CANCELLED", "Operation cancelled."
        else:
            code, message = "FILE_ERROR", "File operation failed; check permissions and free space."
        if json_mode:
            typer.echo(json.dumps({"status": code, "message": message}, ensure_ascii=False))
        else:
            Console(stderr=True, no_color=no_color, markup=False).print(f"{code}: {message}")
        raise typer.Exit(130 if code == "CANCELLED" else 1) from None
