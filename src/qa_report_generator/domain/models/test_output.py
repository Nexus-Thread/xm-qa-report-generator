"""Test output capture model."""

from pydantic import BaseModel, Field, field_validator


class TestOutput(BaseModel):
    """Captured output streams from test execution."""

    stdout: str | None = Field(None, description="Standard output stream")
    stderr: str | None = Field(None, description="Standard error stream")
    log: str | None = Field(None, description="Log output stream")
    __test__ = False

    @field_validator("stdout", "stderr", "log")
    @classmethod
    def normalize_output(cls, v: str | None) -> str | None:
        """Normalize empty output to None and strip trailing whitespace."""
        if v is None:
            return None
        cleaned = v.rstrip()
        return cleaned if cleaned else None
