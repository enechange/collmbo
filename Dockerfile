FROM dhi.io/python:3.14.3-debian13-dev@sha256:c753969eff0a566f02fc13164d69fb55f6a90b72dc2bd6e071129f42fd59c28a AS builder
WORKDIR /build/
COPY --from=ghcr.io/astral-sh/uv:0.10.1@sha256:452e02b117acd2d4eb3ba81a607bed9733b101b6c49492e352b1973463389012 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.3-debian13@sha256:4f2b657d70b0d1e30576718a866332d594627a4b4af1a2d16aaf275e298b0d92 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
