# --- build: resolve deps into a venv with uv ---------------------------------
FROM python:3.12-slim AS build

COPY --from=ghcr.io/astral-sh/uv:0.8 /uv /bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# --- runtime -----------------------------------------------------------------
FROM python:3.12-slim

RUN useradd --create-home --uid 1001 leadlens
WORKDIR /app

COPY --from=build /app/.venv /app/.venv
COPY --chown=leadlens:leadlens . .

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PORT=8000

USER leadlens
EXPOSE 8000

# cloud run sets $PORT. migrations are idempotent so running them on boot is fine
# for a single service - move to a cloud run job once there's more than one instance type
CMD alembic upgrade head && \
    uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --workers 2 --proxy-headers
