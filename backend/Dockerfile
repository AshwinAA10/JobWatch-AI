FROM python:3.13-slim AS base

WORKDIR /app

# Prevent Python from writing bytecode and enable unbuffered standard I/O
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install curl for container healthcheck probe
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Install python runtime dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create a non-privileged system user for container security
RUN groupadd -r jobwatch && useradd -r -g jobwatch -s /bin/false jobwatch

# Copy backend source code
COPY . .

# Set file permissions for the unprivileged user
RUN chown -R jobwatch:jobwatch /app

USER jobwatch

EXPOSE 8000

# Docker container healthcheck against Phase 11 liveness probe
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health/live || exit 1

# Default command: run FastAPI with Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--proxy-headers", "--forwarded-allow-ips", "*"]
