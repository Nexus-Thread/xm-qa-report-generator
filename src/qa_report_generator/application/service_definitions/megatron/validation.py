"""Validation helpers for megatron extraction outputs."""

from __future__ import annotations

from typing import TYPE_CHECKING

from qa_report_generator.application.service_definitions.megatron.schema import MegatronExtractedMetrics

if TYPE_CHECKING:
    from pydantic import BaseModel


def validate_extracted_metrics(model: BaseModel) -> None:
    """Run service-specific validation rules for megatron output."""
    if not isinstance(model, MegatronExtractedMetrics):
        msg = "Unexpected model type for megatron service"
        raise TypeError(msg)

    if model.scenario.max_vus < model.scenario.pre_allocated_vus:
        msg = "maxVUs must be >= preAllocatedVUs"
        raise ValueError(msg)
