FROM ghcr.io/astral-sh/uv:0.13.1 AS uv
FROM python:3.13-slim
COPY --from=uv /uv /usr/local/bin/uv
WORKDIR /app
ENV UV_HTTP_TIMEOUT=300 UV_HTTP_RETRIES=10
COPY apps/api/pyproject.toml apps/api/uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen --no-dev --no-install-project
COPY apps/api/src ./src
ENV PYTHONPATH=/app/src
COPY apps/api/alembic.ini ./
COPY apps/api/migrations ./migrations
RUN useradd --system --uid 10001 oriade
USER oriade
EXPOSE 8000
CMD ["uv", "run", "--no-sync", "uvicorn", "oriade.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-proxy-headers"]
