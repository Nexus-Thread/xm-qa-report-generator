# ── builder stage ─────────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:0.8.22 /uv /bin/uv

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/.venv

# Install third-party dependencies first.
# This layer is cached until pyproject.toml or uv.lock changes —
# source code edits do not bust this layer.
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project

# Copy source and install the project itself as a non-editable wheel.
# Installs qa_report_generator_performance and shared into site-packages,
# so src/ is not required at runtime.
COPY src ./src
RUN uv sync --frozen --no-dev --no-editable

# ── final stage ───────────────────────────────────────────────────────────────
FROM python:3.11-slim AS final

RUN groupadd --gid 1000 appuser \
 && useradd --uid 1000 --gid 1000 --no-create-home --shell /sbin/nologin appuser

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

# Only the pre-built venv is needed; project code lives in site-packages.
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv

# Conventional mount point for k6 report directories passed at runtime.
VOLUME ["/data"]

USER appuser

ENTRYPOINT ["qa-report-generator-performance"]
