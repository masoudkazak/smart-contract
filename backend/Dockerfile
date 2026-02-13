FROM python:3.12-slim as builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip wheel

RUN pip wheel \
    --no-cache-dir \
    --wheel-dir /wheels \
    --index-url https://download.pytorch.org/whl/cpu \
    torch \
    --timeout 300

COPY requirements.txt .
RUN pip wheel \
    --no-cache-dir \
    --wheel-dir /wheels \
    --find-links=/wheels \
    -r requirements.txt


FROM python:3.12-slim

WORKDIR /app

COPY --from=builder /wheels /wheels
COPY --from=builder /build/requirements.txt /tmp/requirements.txt

RUN pip install --upgrade pip && \
    pip install \
      --no-cache-dir \
      --no-index \
      --find-links=/wheels \
      -r /tmp/requirements.txt && \
    rm -rf /wheels /tmp/requirements.txt

COPY . .

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]