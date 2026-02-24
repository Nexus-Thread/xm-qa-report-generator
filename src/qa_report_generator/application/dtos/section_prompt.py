"""Section prompt DTO."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from qa_report_generator.domain.value_objects import SectionType


@dataclass(frozen=True)
class SectionPrompt:
    """Bundles a section's identity with its system prompt."""

    section_type: SectionType
    system_prompt: str
