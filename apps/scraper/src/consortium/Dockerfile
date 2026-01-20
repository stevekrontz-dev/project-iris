# IRIS Search API - Railway Deployment
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy API code
COPY search_api.py .
COPY email_service.py .

# Copy data (lookup + metadata - index will be downloaded at startup)
COPY data/ ./data/

# Expose port
EXPOSE 8000

# Run the API
CMD ["uvicorn", "search_api:app", "--host", "0.0.0.0", "--port", "8000"]
# Build 1768893469
