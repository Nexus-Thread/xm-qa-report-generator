"""Writer adapter for extracted service metrics JSON artifacts."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path


class JsonExtractedMetricsWriter:
    """Write extracted service metrics to a JSON file."""

    def write(self, *, data: dict[str, Any], output_path: Path) -> Path:
        """Persist extracted structured payload to disk."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        return output_path
