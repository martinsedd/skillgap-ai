# Multi-stage build for prod

# Stage 1: Builder
FROM python:3.12-slim AS builder

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*


# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Copy deps files
COPY pyproject.toml uv.lock ./

# Install deps
RUN uv sync --frozen --no-dev

# Stage 2: Runtime
FROM python:3.12-slim

WORKDIR /app

# Install runtime deps only
RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy venv from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY app /app/app
COPY alembic /app/alembic
COPY alembic.ini /app/alembic.ini

# Create non-root user for security
RUN useradd -m -u 1000 skillgap && chown -R skillgap:skillgap /app
USER skillgap

# Set Python path
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app:$PYTHONPATH"

# Expose port
EXPOSE 8000

# Health Check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import httpx; httpx.get('http://localhost:8000/health', timeout=5)"

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
