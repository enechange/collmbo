FROM dhi.io/python:3.14.2-debian13-dev@sha256:32eb03d65667b1fbd186b3019feca362548d5cd868b4c1858fca0139834c02f4 AS builder
WORKDIR /build/
COPY --from=ghcr.io/astral-sh/uv:0.9.26@sha256:9a23023be68b2ed09750ae636228e903a54a05ea56ed03a934d00fe9fbeded4b /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.2-debian13@sha256:2a1e15070c4798908463c6ef43e63cb278fcd27b025e0296e8144a28dff34dbb AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
