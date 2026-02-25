"""Parsed report result DTO."""

from pydantic import BaseModel, Field

from qa_report_generator.domain.models.common.metrics import RunMetrics
from qa_report_generator.domain.models.k6 import K6ReportContext


class ParsedReport(BaseModel):
    """Result of parsing a test report file."""

    metrics: RunMetrics = Field(description="Aggregated test run metrics")
    k6_context: K6ReportContext | None = Field(
        default=None,
        description="k6-specific check and threshold breakdown; None for non-k6 formats",
    )
