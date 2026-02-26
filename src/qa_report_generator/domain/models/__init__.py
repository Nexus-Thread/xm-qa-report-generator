"""Domain models for test run entities and aggregate data.

Structure
---------
common/   Shared models produced and consumed by all source formats (pytest, k6, …).
performance/ Models specific to k6 summary reports; not populated by other parsers.

All public names are re-exported here for backward-compatible imports.
"""

# --- Shared: produced by all parsers ---
from qa_report_generator.domain.models.common.environment import EnvironmentMeta
from qa_report_generator.domain.models.common.failure import Failure
from qa_report_generator.domain.models.common.metrics import RunMetrics
from qa_report_generator.domain.models.common.report_facts import ReportFacts
from qa_report_generator.domain.models.common.test_case import TestCaseResult
from qa_report_generator.domain.models.common.test_output import TestOutput

# --- k6-specific: only populated when parsing k6 summary reports ---
from qa_report_generator.domain.models.performance import K6Check, K6ReportContext, K6SummaryRow, K6Threshold

__all__ = [
    "EnvironmentMeta",
    "Failure",
    "K6Check",
    "K6ReportContext",
    "K6SummaryRow",
    "K6Threshold",
    "ReportFacts",
    "RunMetrics",
    "TestCaseResult",
    "TestOutput",
]
