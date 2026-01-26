FROM dhi.io/python:3.14.2-debian13-dev@sha256:890b25b6d39dfe84eb0b12d9dbd789550df49c5bc377180631932e9459dbcc17 AS builder
WORKDIR /build/
COPY --from=ghcr.io/astral-sh/uv:0.9.26@sha256:9a23023be68b2ed09750ae636228e903a54a05ea56ed03a934d00fe9fbeded4b /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.2-debian13@sha256:50ed864c90492bfb40fb3b2f50f147c2cbd92cf7c4ea27790f945b0357f23caf AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
