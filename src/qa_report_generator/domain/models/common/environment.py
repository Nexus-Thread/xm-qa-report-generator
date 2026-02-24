"""Environment metadata model."""

from pydantic import BaseModel, Field, field_validator


class EnvironmentMeta(BaseModel):
    """Environment and build metadata for the test run."""

    env: str | None = Field(None, description="Environment name (e.g., staging, production)")
    build: str | None = Field(None, description="Build number or version identifier")
    commit: str | None = Field(None, description="Git commit hash or revision")
    target_url: str | None = Field(None, description="Base URL of the system under test")

    @field_validator("env", "build", "commit", "target_url")
    @classmethod
    def _normalize(cls, v: str | None) -> str | None:
        """Strip whitespace and convert empty strings to None."""
        if v is None:
            return None
        return v.strip() or None
