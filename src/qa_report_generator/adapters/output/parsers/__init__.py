"""Report parsing adapters.

Parsers are split into performance (k6) and functional (pytest) submodules.
"""

# Performance parsers (k6)
from qa_report_generator.adapters.output.parsers.performance import K6JsonParser

# Functional parsers (pytest)
from qa_report_generator.adapters.output.parsers.functional import PytestJsonParser

# Legacy imports (from original non-split parsers)
from qa_report_generator.adapters.output.parsers.k6_json_parser import K6JsonParser as K6JsonParserLegacy
from qa_report_generator.adapters.output.parsers.pytest_json_parser import PytestJsonParser as PytestJsonParserLegacy

__all__ = ["K6JsonParser", "PytestJsonParser"]
