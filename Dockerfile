# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install the required packages from requirements.txt
RUN pip install --no-cache-dir -r requirement.txt

# Expose the port the Flask app will run on
EXPOSE 5000

# Set environment variables for Redis (default values)
ENV CACHE_REDIS_URL redis://redis:6379/0
ENV CELERY_BROKER_URL redis://redis:6379/1
ENV CELERY_RESULT_BACKEND redis://redis:6379/1

# Run the Flask application
CMD ["flask", "run", "--host=0.0.0.0"]
