"""Domain models representing test run entities and aggregate data."""

from qa_report_generator.domain.models.environment import EnvironmentMeta
from qa_report_generator.domain.models.failure import Failure
from qa_report_generator.domain.models.metrics import RunMetrics
from qa_report_generator.domain.models.report_facts import ReportFacts
from qa_report_generator.domain.models.test_case import TestCaseResult
from qa_report_generator.domain.models.test_output import TestOutput

__all__ = [
    "EnvironmentMeta",
    "Failure",
    "ReportFacts",
    "RunMetrics",
    "TestCaseResult",
    "TestOutput",
]
