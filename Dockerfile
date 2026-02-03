FROM dhi.io/python:3.14.2-debian13-dev@sha256:dd916fef1499eecf0a2c27b65050943538ac8a48ef9695d546526982bf1974a9 AS builder
WORKDIR /build/
COPY --from=ghcr.io/astral-sh/uv:0.9.29@sha256:db9370c2b0b837c74f454bea914343da9f29232035aa7632a1b14dc03add9edb /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.2-debian13@sha256:41084dfc5e56316e9b2d4c474774dad61b7a4c709d05040ab3b9c822791ac94e AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
