# syntax=docker/dockerfile:1
FROM python:3.11-slim AS builder

WORKDIR /build

# Install uv from official binary image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy dependency files
COPY pyproject.toml uv.lock README.md ./

# Create virtual environment and install production dependencies
RUN uv venv /opt/venv && \
    uv sync --frozen --no-dev

# Final runtime image
FROM python:3.11-slim AS runtime

WORKDIR /app

# Create unprivileged user and group
RUN groupadd -g 10001 excelpilot && \
    useradd -u 10001 -g excelpilot -m -d /home/excelpilot -s /bin/bash excelpilot && \
    mkdir -p /data && \
    chown -R excelpilot:excelpilot /data /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy source code and package metadata
COPY pyproject.toml README.md ./
COPY src/ src/

# Set environment variables
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    EXCELPILOT_DATA_DIR=/data

# Install package in editable mode inside venv without downloading extra dependencies
RUN /opt/venv/bin/pip install --no-deps -e .

USER excelpilot

VOLUME ["/data"]

ENTRYPOINT ["excelpilot"]
CMD ["--help"]
