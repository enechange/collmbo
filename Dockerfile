FROM python:3.13.9-slim-trixie AS builder
WORKDIR /build/
COPY --from=ghcr.io/astral-sh/uv:0.9.14 /uv /usr/local/bin/uv
COPY pyproject.toml /build/
RUN uv pip install --system -r pyproject.toml --no-cache

FROM python:3.13.9-slim-trixie AS app
WORKDIR /app/
COPY --from=builder /usr/local/bin/ /usr/local/bin/
COPY --from=builder /usr/local/lib/ /usr/local/lib/
RUN pip install --upgrade pip==25.3
COPY config/ /app/config/
COPY main.py /app/
COPY app/*.py /app/app/
COPY app/mcp/*.py /app/app/mcp/
ENTRYPOINT [ "python", "main.py" ]
