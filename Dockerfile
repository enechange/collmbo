FROM dhi.io/python:3.14.2-debian13-dev@sha256:74c05b08591bd865dd1a105af3a1353467f12510c7094162607742450f7969c9 AS builder
WORKDIR /build/
COPY --from=ghcr.io/astral-sh/uv:0.9.26@sha256:9a23023be68b2ed09750ae636228e903a54a05ea56ed03a934d00fe9fbeded4b /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.2-debian13@sha256:c055b3667bbfaac0e8e8ef77b0105c6581817e8b05e437352eedab0819e2c2cc AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
