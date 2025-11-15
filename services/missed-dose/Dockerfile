# Use Python 3.12 slim image for Cloud Run (ADK requires 3.12+)
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
# Workaround for opentelemetry-sdk version conflict with ADK 1.17.0
# Install ADK dependencies manually to avoid conflicts
# See: docs/installation/dependency-conflict-workaround.md
COPY requirements.txt .
RUN pip install --no-cache-dir --no-deps google-adk==1.17.0 && \
    pip install --no-cache-dir \
        "opentelemetry-sdk==1.37.0" \
        "opentelemetry-api==1.37.0" \
        "opentelemetry-exporter-otlp-proto-http==1.37.0" \
        "google-generativeai>=0.8.3" \
        "google-genai>=1.0.0" \
        "absolufy-imports>=0.3.1,<1.0.0" \
        "anyio>=4.9.0,<5.0.0" \
        "authlib>=1.5.1,<2.0.0" \
        "click>=8.1.8,<9.0.0" \
        "fastapi>=0.115.0,<1.0.0" \
        "graphviz>=0.20.2,<1.0.0" \
        "mcp>=1.8.0,<2.0.0" \
        "pydantic>=2.0,<3.0.0" \
        "python-dateutil>=2.9.0.post0,<3.0.0" \
        "python-dotenv>=1.0.0,<2.0.0" \
        "PyYAML>=6.0.2,<7.0.0" \
        "requests>=2.32.4,<3.0.0" \
        "sqlalchemy>=2.0,<3.0.0" \
        "starlette>=0.46.2,<1.0.0" \
        "tenacity>=8.0.0,<9.0.0" && \
    pip install --no-cache-dir \
        Flask==3.0.0 \
        flask-cors>=4.0.2 \
        google-cloud-firestore==2.13.0 \
        gunicorn>=23.0.0 \
        docstring_parser \
        google-api-core \
        google-auth \
        google-cloud-bigquery \
        google-cloud-resource-manager \
        google-cloud-storage \
        google-cloud-discoveryengine \
        grpc-google-iam-v1 \
        packaging \
        proto-plus \
        protobuf \
        shapely && \
    pip install --no-cache-dir --no-deps google-cloud-aiplatform>=1.121.0

# Copy service files
COPY main.py .

# Copy templates and static files for web interface
COPY templates/ ./templates/
COPY static/ ./static/

# Copy ADK agents and config from parent directory
# (deploy.sh will copy these before build)
COPY services/ ./services/

# Copy SRTR data files
# (deploy.sh will copy these before build)
COPY data/ ./data/

# Set environment variables
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

# Run with gunicorn for production
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app
