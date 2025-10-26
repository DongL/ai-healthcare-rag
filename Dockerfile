# ==============================
# RAG Healthcare Production Dockerfile
# ==============================

# Build stage
FROM python:3.10-slim AS builder

WORKDIR /app

# Install build dependencies and uv
RUN apt-get update && \
    apt-get install -y --no-install-recommends --fix-missing \
    gcc \
    g++ \
    curl \
    ca-certificates && \
    curl -LsSf https://astral.sh/uv/install.sh | sh && \
    ln -s /root/.local/bin/uv /usr/local/bin/uv && \
    apt-get remove -y curl && \
    rm -rf /var/lib/apt/lists/*

# Copy and install dependencies with uv (10-100x faster than pip)
COPY requirements.txt .
ENV UV_HTTP_TIMEOUT=300
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system --index-strategy unsafe-best-match -r requirements.txt


# Runtime stage
FROM python:3.10-slim

# Create non-root user with home directory
RUN groupadd -r appuser && useradd -r -g appuser -m appuser

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=appuser:appuser . .

# Production environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PORT=8000 \
    HF_HOME=/home/appuser/.cache/huggingface \
    TRANSFORMERS_CACHE=/home/appuser/.cache/huggingface

# Security: Don't run as root
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

EXPOSE ${PORT}

# Use production ASGI server with proper workers
CMD uvicorn rag_app:app \
    --host 0.0.0.0 \
    --port ${PORT} \
    --workers 4 \
    --loop uvloop \
    --log-level info \
    --access-log \
    --no-server-header
