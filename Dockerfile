FROM dhi.io/python:3.14.3-debian13-dev@sha256:d234c828d1ce953bb72747a8a21929bff3f9dcbcf62241bc2d79798ecdb1742d AS builder
WORKDIR /build/
COPY --from=ghcr.io/astral-sh/uv:0.10.0@sha256:78a7ff97cd27b7124a5f3c2aefe146170793c56a1e03321dd31a289f6d82a04f /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.3-debian13@sha256:c1c98a9135f408a8accf6c78984b3d5c553378db04bea4fb0729ddfa9593e5cc AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
