FROM dhi.io/python:3.14.2-debian13-dev@sha256:dc568a225448908b211d1854f23f9da4825eac16f4db3a7c26199ba4c9db95c9 AS builder
WORKDIR /build/
COPY --from=ghcr.io/astral-sh/uv:0.9.28@sha256:59240a65d6b57e6c507429b45f01b8f2c7c0bbeee0fb697c41a39c6a8e3a4cfb /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.2-debian13@sha256:01c97484fa6477fa64d81593df30a97ef50eabc695390b015eaca37a61f67644 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
