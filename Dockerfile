# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Install Redis
RUN apt-get update && \
    apt-get install -y redis-server && \
    rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=script.py \
    CACHE_REDIS_URL=redis://localhost:6379/0 \
    CELERY_BROKER_URL=redis://localhost:6379/1 \
    CELERY_RESULT_BACKEND=redis://localhost:6379/1

# Set the working directory inside the container
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
# COPY .env .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install python-dotenv

# Copy the rest of the application
COPY . .

# Create a startup script
RUN echo '#!/bin/bash\nredis-server --daemonize yes\nflask run --host=0.0.0.0 --port=$PORT' > start.sh && \
    chmod +x start.sh

# Run the startup script
CMD ["./start.sh"]