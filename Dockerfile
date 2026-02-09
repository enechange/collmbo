FROM dhi.io/python:3.14.3-debian13-dev@sha256:0e33d44383fdb4b8a090e1bb6f3ef5678e861d3e9dec84948834c566d24c5dc8 AS builder
WORKDIR /build/
COPY --from=ghcr.io/astral-sh/uv:0.10.0@sha256:78a7ff97cd27b7124a5f3c2aefe146170793c56a1e03321dd31a289f6d82a04f /uv /usr/local/bin/uv
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
