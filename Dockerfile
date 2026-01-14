FROM dhi.io/python:3.14.2-debian13-dev@sha256:32eb03d65667b1fbd186b3019feca362548d5cd868b4c1858fca0139834c02f4 AS builder
WORKDIR /build/
COPY --from=ghcr.io/astral-sh/uv:0.9.25@sha256:13e233d08517abdafac4ead26c16d881cd77504a2c40c38c905cf3a0d70131a6 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.2-debian13@sha256:2a1e15070c4798908463c6ef43e63cb278fcd27b025e0296e8144a28dff34dbb AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/*.py /app/app/
COPY app/mcp/*.py /app/app/mcp/
ENTRYPOINT [ "python", "main.py" ]
