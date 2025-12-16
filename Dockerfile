FROM python:3.9-slim

WORKDIR /app

# Install system dependencies if needed (e.g., git for gitpython)
RUN apt-get update && apt-get install -y git curl && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ src/
COPY run_api.py .
COPY .env.example .env.example

# Set PYTHONPATH
ENV PYTHONPATH=/app/src

# Set HOST for Docker (bind to all interfaces)
ENV HOST=0.0.0.0

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/ || exit 1

# Run the FastAPI application
CMD ["python", "run_api.py"]
