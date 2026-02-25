"""k6-specific report context."""

from pydantic import BaseModel, Field


class K6ReportContext(BaseModel):
    """Breakdown of k6 check and threshold results."""

    checks_total: int = Field(ge=0, description="Total number of checks executed")
    checks_passed: int = Field(ge=0, description="Number of checks that passed")
    checks_failed: int = Field(ge=0, description="Number of checks that failed")
    thresholds_total: int = Field(ge=0, description="Total number of thresholds evaluated")
    thresholds_passed: int = Field(ge=0, description="Number of thresholds that passed")
    thresholds_failed: int = Field(ge=0, description="Number of thresholds that were violated")
