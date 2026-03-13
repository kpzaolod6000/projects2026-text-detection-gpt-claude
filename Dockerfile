# ── Stage 1: builder ──────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

COPY requirements.txt .

RUN python -m venv /venv && \
    /venv/bin/pip install --upgrade pip --quiet && \
    /venv/bin/pip install --no-cache-dir -r requirements.txt --quiet

# ── Stage 2: runtime ──────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/venv/bin:$PATH"

WORKDIR /app

# Install Tesseract OCR + English language data + fonts for PIL annotation
RUN apt-get update && apt-get install -y --no-install-recommends \
        tesseract-ocr \
        tesseract-ocr-eng \
        fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /venv /venv

# Copy application source
COPY src/ ./src/
COPY run.sh .

RUN chmod +x run.sh && \
    mkdir -p images output/annotated

ENTRYPOINT ["./run.sh"]
