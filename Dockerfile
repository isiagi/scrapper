# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=script.py \
    CACHE_REDIS_URL=redis://redis:6379/0 \
    CELERY_BROKER_URL=redis://redis:6379/1 \
    CELERY_RESULT_BACKEND=redis://redis:6379/1

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies
# RUN apt-get update \
#     && apt-get install -y --no-install-recommends gcc \
#     && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
COPY .env .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install python-dotenv

# Copy the rest of the application
COPY . .

# Expose the port the Flask app will run on
EXPOSE 5000

# Run the Flask application
CMD ["flask", "run", "--host=0.0.0.0"]