"""Core domain value objects."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EnvironmentMeta:
    """Environment metadata attached to generated reports."""

    env: str | None = None
    build: str | None = None
    commit: str | None = None
    target_url: str | None = None
