FROM python:3.9-slim

WORKDIR /app

# Install system dependencies if needed (e.g., git for gitpython)
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ src/
COPY .env.example .env.example

# Set PYTHONPATH
ENV PYTHONPATH=/app/src

# Expose port
EXPOSE 8080

# Run the application
CMD ["python", "-m", "automation_agent.main"]
