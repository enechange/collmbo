FROM python:3.13.7-slim-trixie AS builder
WORKDIR /build/
COPY uv-requirements.txt /build/
RUN pip install --no-cache-dir -r uv-requirements.txt
COPY requirements.txt /build/
RUN uv pip install --system --no-cache -r requirements.txt

FROM python:3.13.7-slim-trixie AS app
WORKDIR /app/
COPY --from=builder /usr/local/bin/ /usr/local/bin/
COPY --from=builder /usr/local/lib/ /usr/local/lib/
COPY config/ /app/config/
COPY main.py /app/
COPY app/*.py /app/app/
COPY app/mcp/*.py /app/app/mcp/
ENTRYPOINT [ "python", "main.py" ]
