FROM dhi.io/python:3.14.3-debian13-dev@sha256:0e33d44383fdb4b8a090e1bb6f3ef5678e861d3e9dec84948834c566d24c5dc8 AS builder
WORKDIR /build/
COPY --from=ghcr.io/astral-sh/uv:0.10.0@sha256:78a7ff97cd27b7124a5f3c2aefe146170793c56a1e03321dd31a289f6d82a04f /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.3-debian13@sha256:5c16260e902c076877cc7c5b4f33dea2e96f2b8a43dc980d80a5ae7cdff372cc AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
