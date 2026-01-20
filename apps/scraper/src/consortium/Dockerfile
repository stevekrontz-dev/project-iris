# IRIS Search API - Railway Deployment with LFS support
# Multi-stage build to properly fetch Git LFS objects

# Stage 1: Clone repo with LFS
FROM alpine/git:latest AS lfs-fetch
RUN apk add --no-cache git-lfs
WORKDIR /repo
# Clone with LFS - use build arg for repo URL
ARG REPO_URL=https://github.com/stevekrontz-dev/project-iris.git
ARG BRANCH=main
RUN git lfs install && \
    git clone --depth 1 --branch ${BRANCH} ${REPO_URL} . && \
    git lfs pull

# Stage 2: Python runtime
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy API code from build context
COPY search_api.py .
COPY email_service.py .

# Copy data from LFS-fetched repo (Stage 1)
COPY --from=lfs-fetch /repo/apps/scraper/src/consortium/data/ ./data/

# Expose port
EXPOSE 8000

# Run the API
CMD ["uvicorn", "search_api:app", "--host", "0.0.0.0", "--port", "8000"]
