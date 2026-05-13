# ============================================
# BeaverChain Multi-Stage Dockerfile
# Supports: Python Backend + Go Services + Frontend
# ============================================

# ---------- Builder Stage: Frontend ----------
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# ---------- Builder Stage: Go Services ----------
FROM golang:1.22-alpine AS go-builder
WORKDIR /app

RUN apk add --no-cache git ca-certificates tzdata

# Copy go modules and download dependencies
COPY go.mod go.sum ./
RUN go mod download

# Build all Go services
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o /bin/prompt-engine ./prompt_engine
RUN CGO_ENABLED=0 GOOS=linux go build -o /bin/guardrails ./guardrails
RUN CGO_ENABLED=0 GOOS=linux go build -o /bin/workflow-orchestration ./workflow_orchestration

# ---------- Builder Stage: Python Backend ----------
FROM python:3.11-slim AS python-builder
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY model_registry/requirements.txt ./model_registry/
COPY optimization_toolchain/requirements.txt ./optimization_toolchain/

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r model_registry/requirements.txt && \
    pip install --no-cache-dir -r optimization_toolchain/requirements.txt

# Copy Python code
COPY model_registry/ ./model_registry/
COPY optimization_toolchain/ ./optimization_toolchain/

# ---------- Final Production Stage ----------
FROM python:3.11-slim AS production
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    ca-certificates \
    tzdata \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy from frontend builder
COPY --from=frontend-builder /app/frontend/dist /usr/share/nginx/html

# Copy from go builder
COPY --from=go-builder /bin/* /usr/local/bin/
COPY --from=go-builder /usr/share/zoneinfo /usr/share/zoneinfo

# Copy from python builder
COPY --from=python-builder /app /app
COPY --from=python-builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# Nginx configuration
COPY docker/nginx.conf /etc/nginx/nginx.conf

# Expose ports
EXPOSE 80 8000 8001 8002 8003

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:80/health || exit 1

# Entrypoint script
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
