FROM python:3.13.10-slim-trixie AS builder
WORKDIR /build/
COPY --from=ghcr.io/astral-sh/uv:0.9.16 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM python:3.13.10-slim-trixie AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/*.py /app/app/
COPY app/mcp/*.py /app/app/mcp/
ENTRYPOINT [ "python", "main.py" ]
