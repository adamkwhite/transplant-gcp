# Use Python 3.12 slim image for Cloud Run (ADK requires 3.12+)
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service files
COPY main.py .

# Copy ADK agents and config from parent directory
# (deploy.sh will copy these before build)
COPY services/ ./services/

# Set environment variables
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

# Run with gunicorn for production
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app
