FROM dhi.io/python:3.14.2-debian13-dev@sha256:890b25b6d39dfe84eb0b12d9dbd789550df49c5bc377180631932e9459dbcc17 AS builder
WORKDIR /build/
COPY --from=ghcr.io/astral-sh/uv:0.9.27@sha256:143b40f4ab56a780f43377604702107b5a35f83a4453daf1e4be691358718a6a /uv /usr/local/bin/uv
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
