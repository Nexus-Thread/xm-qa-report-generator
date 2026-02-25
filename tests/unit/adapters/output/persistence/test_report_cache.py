"""Unit tests for the filesystem report cache."""

from __future__ import annotations

from pathlib import Path

import pytest

from qa_report_generator.adapters.output.persistence.cache import FileReportCache
from qa_report_generator.domain.exceptions import PersistenceError
from qa_report_generator.domain.models import EnvironmentMeta, RunMetrics
from qa_report_generator.domain.value_objects import Duration


def _make_metrics() -> RunMetrics:
    return RunMetrics(
        total=1,
        passed=1,
        failed=0,
        skipped=0,
        errors=0,
        duration=Duration(seconds=1.0),
        failures=[],
    )


def test_cache_roundtrip(tmp_path: Path) -> None:
    """Cache should round-trip metrics and metadata."""
    cache = FileReportCache(tmp_path)
    report_path = tmp_path / "report.json"
    report_path.write_text("{}", encoding="utf-8")

    metrics = _make_metrics()
    environment = EnvironmentMeta(env="test", build="1", commit=None, target_url=None)
    cache.save_cached_facts(report_path, metrics, environment, [str(report_path)])

    cached = cache.load_cached_facts(report_path)

    assert cached is not None
    cached_metrics, _k6_context, cached_env, cached_inputs = cached
    assert cached_metrics.total == metrics.total
    assert cached_env.env == environment.env
    assert cached_inputs == [str(report_path)]


def test_cache_miss_returns_none(tmp_path: Path) -> None:
    """Missing cache file should return None."""
    cache = FileReportCache(tmp_path)
    report_path = tmp_path / "missing.json"

    cached = cache.load_cached_facts(report_path)

    assert cached is None


def test_cache_corrupt_payload_raises(tmp_path: Path) -> None:
    """Corrupt cache payload should raise PersistenceError."""
    cache = FileReportCache(tmp_path)
    report_path = tmp_path / "report.json"
    report_path.write_text("{}", encoding="utf-8")
    cache_path = tmp_path / f"{report_path.resolve().as_posix().replace('/', '_')}.json"
    cache_path.write_text("{not json", encoding="utf-8")

    with pytest.raises(PersistenceError):
        cache.load_cached_facts(report_path)


def test_cache_invalid_schema_raises(tmp_path: Path) -> None:
    """Invalid cache payload shape should raise PersistenceError."""
    cache = FileReportCache(tmp_path)
    report_path = tmp_path / "report.json"
    report_path.write_text("{}", encoding="utf-8")
    cache_path = tmp_path / f"{report_path.resolve().as_posix().replace('/', '_')}.json"
    cache_path.write_text("{}", encoding="utf-8")

    with pytest.raises(PersistenceError):
        cache.load_cached_facts(report_path)


def test_cache_save_handles_filesystem_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Filesystem write errors should raise PersistenceError."""
    cache = FileReportCache(tmp_path)
    report_path = tmp_path / "report.json"
    report_path.write_text("{}", encoding="utf-8")
    metrics = _make_metrics()
    environment = EnvironmentMeta(env="test", build="1", commit=None, target_url=None)

    def _raise_error(*_: object, **__: object) -> None:
        msg = "boom"
        raise OSError(msg)

    monkeypatch.setattr(Path, "write_text", _raise_error)

    with pytest.raises(PersistenceError):
        cache.save_cached_facts(report_path, metrics, environment, [str(report_path)])


def test_cache_path_traversal_protection(tmp_path: Path) -> None:
    """Cache should prevent path traversal attacks."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    cache = FileReportCache(cache_dir)

    # Normal case should work
    report_path = tmp_path / "report.json"
    report_path.write_text("{}", encoding="utf-8")
    metrics = _make_metrics()
    environment = EnvironmentMeta(env="test", build="1", commit=None, target_url=None)

    # This should succeed without errors
    cache.save_cached_facts(report_path, metrics, environment, [str(report_path)])
    cached = cache.load_cached_facts(report_path)
    assert cached is not None

    # Path traversal attempt should be caught (the cache path sanitization
    # ensures all paths are transformed into safe filenames within cache_dir)
    # The current implementation uses resolve().as_posix().replace("/", "_")
    # which effectively prevents traversal by flattening the path
    evil_path = tmp_path / ".." / ".." / "etc" / "passwd"

    # Should work but the cache file will be in the cache directory
    cache.save_cached_facts(evil_path, metrics, environment, [str(evil_path)])
    cached = cache.load_cached_facts(evil_path)
    assert cached is not None

    # Verify the cache file is indeed within cache_dir
    cache_path = cache._cache_path(evil_path)  # noqa: SLF001
    assert cache_path.resolve().is_relative_to(cache_dir.resolve())
