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

# Create non-root user and groups FIRST (using different UID/GID to avoid conflicts)
RUN groupadd -g 1000 mcpuser && \
    groupadd -g 999 docker || true && \
    useradd -r -u 1000 -g mcpuser mcpuser && \
    usermod -a -G docker mcpuser || true

# Copy Python packages from builder
COPY --from=builder /root/.local /home/mcpuser/.local

# Create application directories and set ownership
RUN mkdir -p /app/data /app/config /app/logs && \
    chown -R mcpuser:mcpuser /app

# Copy application code
COPY --chown=mcpuser:mcpuser src/ /app/src/
COPY --chown=mcpuser:mcpuser utils/ /app/utils/
COPY --chown=mcpuser:mcpuser config/ /app/config/
COPY --chown=mcpuser:mcpuser scripts/ /app/scripts/

# Set working directory
WORKDIR /app

# Switch to non-root user
USER mcpuser

# Add local bin to PATH
ENV PATH=/home/mcpuser/.local/bin:$PATH

# Expose port for HTTP interface
EXPOSE 9090

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:9090/health || exit 1

# Start command - use dual-mode server for both MCP and HTTP
CMD ["python", "/app/src/dual_server.py"]