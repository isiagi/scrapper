# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Install Redis
RUN apt-get update && \
    apt-get install -y redis-server && \
    rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=src/script \
    PYTHONPATH=/app \
    CACHE_REDIS_URL=redis://localhost:6379/0 \
    CELERY_BROKER_URL=redis://localhost:6379/1 \
    CELERY_RESULT_BACKEND=redis://localhost:6379/1 \
    FLASK_DEBUG=1

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

# Configure Redis to listen on all interfaces
RUN sed -i 's/bind 127.0.0.1/bind 0.0.0.0/g' /etc/redis/redis.conf && \
    sed -i 's/protected-mode yes/protected-mode no/g' /etc/redis/redis.conf

# Create a startup script with debug logging
RUN echo '#!/bin/bash\n\
echo "Starting Redis server..."\n\
redis-server /etc/redis/redis.conf --daemonize yes\n\
echo "Waiting for Redis to start..."\n\
sleep 2\n\
echo "Testing Redis connection..."\n\
redis-cli ping\n\
echo "Starting Flask application..."\n\
echo "Current directory: $(pwd)"\n\
echo "Python path: $PYTHONPATH"\n\
echo "Flask app: $FLASK_APP"\n\
python -m flask run --host=0.0.0.0 --port=$PORT' > start.sh && \
    chmod +x start.sh

# Run the startup script
CMD ["./start.sh"]