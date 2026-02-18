# ═══════════════════════════════════════════════════════════════════════════
# Smart Money Platform — Production Docker Build
# Multi-stage build for optimized image size
# ═══════════════════════════════════════════════════════════════════════════

# ── Stage 1: Builder ──────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install to a virtual environment
COPY requirements.txt .
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# ── Stage 2: Runtime ─────────────────────────────────────────────────────
FROM python:3.12-slim

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* && \
    # Create non-root user
    useradd -m -u 1000 -s /bin/bash appuser && \
    # Create necessary directories
    mkdir -p /app/data /app/logs /app/frontend/static && \
    chown -R appuser:appuser /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY --chown=appuser:appuser api/ /app/api/
COPY --chown=appuser:appuser frontend/ /app/frontend/
COPY --chown=appuser:appuser requirements.txt /app/

# Switch to non-root user
USER appuser

# Expose port (configurable via PORT env var, default 8502)
EXPOSE 8502

# Health check — uses PORT env var
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8502}/api/health || exit 1

# Calculate optimal workers based on CPU cores (2 * cores + 1)
# Default to 3 workers if can't determine
ENV WORKERS=3

# Run uvicorn with production settings
CMD ["sh", "-c", "workers=$(python -c 'import os; print(min(2 * os.cpu_count() + 1, 8) if os.cpu_count() else 3)' 2>/dev/null || echo 3); exec uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8502} --workers $workers --log-level info --access-log --proxy-headers --forwarded-allow-ips='*'"]
