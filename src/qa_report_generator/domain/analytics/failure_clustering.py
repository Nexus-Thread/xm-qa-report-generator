"""Cluster failures by similarity."""

from __future__ import annotations

from difflib import SequenceMatcher
from typing import TYPE_CHECKING

from qa_report_generator.domain.analytics.models import FailureCluster

if TYPE_CHECKING:
    from qa_report_generator.domain.models import Failure


class FailureClusterer:
    """Cluster failures based on message similarity."""

    def cluster_by_message_similarity(
        self,
        failures: list[Failure],
        threshold: float = 0.7,
    ) -> list[FailureCluster]:
        """Cluster failures by error message similarity."""
        clusters: list[FailureCluster] = []
        unassigned = failures.copy()

        while unassigned:
            seed = unassigned.pop(0)
            cluster = [seed]
            remaining: list[Failure] = []
            for failure in unassigned:
                similarity = self._message_similarity(seed.message, failure.message)
                if similarity >= threshold:
                    cluster.append(failure)
                else:
                    remaining.append(failure)

            unassigned = remaining
            clusters.append(
                FailureCluster(
                    representative=seed,
                    failures=cluster,
                    count=len(cluster),
                ),
            )

        return clusters

    @staticmethod
    def _message_similarity(message_a: str, message_b: str) -> float:
        return SequenceMatcher(None, message_a, message_b).ratio()
