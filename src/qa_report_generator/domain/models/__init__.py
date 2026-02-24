"""Domain models for test run entities and aggregate data.

Structure
---------
common/   Shared models produced and consumed by all source formats (pytest, k6, …).
pytest/   Models specific to pytest JSON reports; not populated by other parsers.

All public names are re-exported here for backward-compatible imports.
"""

# --- Shared: produced by all parsers ---
from qa_report_generator.domain.models.common.environment import EnvironmentMeta
from qa_report_generator.domain.models.common.failure import Failure
from qa_report_generator.domain.models.common.metrics import RunMetrics
from qa_report_generator.domain.models.common.report_facts import ReportFacts
from qa_report_generator.domain.models.common.test_case import TestCaseResult

# --- pytest-specific: only populated when parsing pytest JSON reports ---
from qa_report_generator.domain.models.pytest.test_output import TestOutput

__all__ = [
    # Shared
    "EnvironmentMeta",
    "Failure",
    "ReportFacts",
    "RunMetrics",
    "TestCaseResult",
    # pytest-specific
    "TestOutput",
]
