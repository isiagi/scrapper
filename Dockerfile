# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=src/script \
    PYTHONPATH=/app \
    CACHE_REDIS_URL=redis://localhost:6379/0 \
    CELERY_BROKER_URL=redis://localhost:6379/1 \
    CELERY_RESULT_BACKEND=redis://localhost:6379/1 \
    FLASK_DEBUG=1 \
    PORT=5000

# Install Chrome and dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    curl \
    unzip \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy the current directory contents into the container
COPY . /app

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install python-dotenv

# Expose port
EXPOSE 5000

# Set Redis environment variables
ENV CACHE_REDIS_URL redis://redis:6379/0
ENV CELERY_BROKER_URL redis://redis:6379/1
ENV CELERY_RESULT_BACKEND redis://redis:6379/1

CMD ["flask", "run", "--host=0.0.0.0"]