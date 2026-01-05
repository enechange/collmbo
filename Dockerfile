FROM dhi.io/python:3.14.2-debian13-dev@sha256:84c62df9f2a1fe35903c347a7c05fe8b62484baa49c40b1005f7b5c0c88b10f6 AS builder
WORKDIR /build/
COPY --from=ghcr.io/astral-sh/uv:0.9.21@sha256:4c55b48c2750a257fa631f31d8362445d9f880ba219d871c33153b165a83c81a /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.2-debian13@sha256:f7dda626c48d33c069bb7183063eda9190f4d3d62d292736b74ce19bea9ac72e AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/*.py /app/app/
COPY app/mcp/*.py /app/app/mcp/
ENTRYPOINT [ "python", "main.py" ]
