FROM ghcr.io/astral-sh/uv:0.13.1 AS uv
FROM python:3.12.15-slim-bookworm
COPY --from=uv /uv /usr/local/bin/uv
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 UV_LINK_MODE=copy
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project
COPY services ./services
COPY scripts ./scripts
COPY config ./config
COPY tests ./tests
COPY alembic.ini ./
RUN uv sync --frozen && useradd --uid 10001 --create-home app \
    && mkdir -p /app/state && chown -R app:app /app
ENV PATH="/app/.venv/bin:$PATH"
USER app
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "services.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
