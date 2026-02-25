"""Configuration for the narrative adapter."""

from pydantic import BaseModel, ConfigDict, field_validator


class NarrativeAdapterConfig(BaseModel):
    """Configuration for the narrative adapter."""

    model_config = ConfigDict(extra="ignore")

    llm_model: str

    @field_validator("llm_model")
    @classmethod
    def validate_model(cls, v: str) -> str:
        """Ensure model name is not empty."""
        v = v.strip()
        if not v:
            msg = "llm_model cannot be empty. Check .env file."
            raise ValueError(msg)
        return v
