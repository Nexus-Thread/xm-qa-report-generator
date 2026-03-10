"""CLI output helpers for k6 extraction commands."""

import json

import typer


def print_json_output(*, success_message: str, payload: object, heading: str | None = None) -> None:
    """Print success text and JSON payload."""
    typer.secho(f"✅ {success_message}", fg=typer.colors.GREEN)
    if heading:
        typer.echo(heading)
    typer.echo(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
