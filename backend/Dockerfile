# Use Python 3.11 slim image for smaller size

FROM python:3.11-slim

 

# Set working directory

WORKDIR /app

 

# Install system dependencies

RUN apt-get update && apt-get install -y \

    gcc \

    postgresql-client \

    curl \

    && rm -rf /var/lib/apt/lists/*

 

# Copy requirements first for better caching

COPY requirements.txt .

 

# Install Python dependencies

RUN pip install --no-cache-dir -r requirements.txt && \

    pip install --no-cache-dir gunicorn

 

# Copy application code

COPY . .

 

# Create non-root user for security

RUN useradd -m -u 1000 appuser && \

    chown -R appuser:appuser /app && \

    mkdir -p /app/logs && \

    chown -R appuser:appuser /app/logs

 

# Switch to non-root user

USER appuser

 

# Expose port

EXPOSE 5001

 

# Health check

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \

    CMD curl -f http://localhost:5001/health || exit 1

 

# Start command with database migration

CMD flask db upgrade && \

    gunicorn --bind 0.0.0.0:5001 \

    --workers 4 \

    --timeout 120 \

    --access-logfile /app/logs/access.log \

    --error-logfile /app/logs/error.log \

    --log-level info \

    app:app