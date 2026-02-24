"""Report parsing adapters."""

from qa_report_generator.adapters.output.parsers.k6_json_parser import K6JsonParser
from qa_report_generator.adapters.output.parsers.pytest_json_parser import PytestJsonParser

__all__ = ["K6JsonParser", "PytestJsonParser"]
