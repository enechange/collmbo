FROM dhi.io/python:3.14.3-debian13-dev@sha256:6c1502bbc5f233550ca0c0c9c06299c53d048bb5e71500058320d98bf33f1e26 AS builder
WORKDIR /build/
COPY --from=ghcr.io/astral-sh/uv:0.9.30@sha256:538e0b39736e7feae937a65983e49d2ab75e1559d35041f9878b7b7e51de91e4 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.3-debian13@sha256:a156890ce30519ddf34a88b6c5b60b4b67c13b4a4b8cb764e3c1f8490081d7e3 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
