# Multi-stage build for optimized container
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements /tmp/
RUN pip install --no-cache-dir --user -r /tmp/requirements

# Runtime stage
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    smartmontools \
    lm-sensors \
    iotop \
    htop \
    curl \
    jq \
    net-tools \
    procps \
    docker.io \
    rsync \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user and groups
RUN groupadd -g 999 mcpuser && \
    groupadd -g 998 docker || true && \
    useradd -r -u 999 -g mcpuser mcpuser && \
    usermod -a -G docker mcpuser || true

# Copy Python packages from builder
COPY --from=builder /root/.local /home/mcpuser/.local

# Create application directories
RUN mkdir -p /app/data /app/config /app/logs && \
    chown -R mcpuser:mcpuser /app

# Copy application code
COPY --chown=mcpuser:mcpuser src/ /app/src/
COPY --chown=mcpuser:mcpuser config/ /app/config/
COPY --chown=mcpuser:mcpuser scripts/ /app/scripts/

# Set working directory
WORKDIR /app

# Switch to non-root user
USER mcpuser

# Add local bin to PATH
ENV PATH=/home/mcpuser/.local/bin:$PATH

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python /app/scripts/health_check.py || exit 1

# Start command
CMD ["python", "/app/src/main.py"]