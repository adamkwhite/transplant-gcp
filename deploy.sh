#!/bin/bash

# Google Cloud Run Deployment Script
# For the Google Cloud Run Hackathon

set -e

echo "🚀 Google Cloud Run Deployment - Transplant Medication Adherence"
echo "============================================================"

# Configuration
PROJECT_ID="transplant-prediction"
REGION="us-central1"
SERVICE_NAME="missed-dose-service"

# Ensure we're using the right project
gcloud config set project $PROJECT_ID

echo ""
echo "📦 Preparing deployment..."

# Copy gemini_client to the service directory for Docker build
cp services/gemini_client.py services/missed-dose/

# Deploy to Cloud Run
echo "🔨 Building and deploying to Cloud Run..."
echo "This will build the container and deploy in one step..."

cd services/missed-dose

# Deploy with source (builds automatically)
gcloud run deploy $SERVICE_NAME \
    --source . \
    --region $REGION \
    --allow-unauthenticated \
    --memory 512Mi \
    --cpu 1 \
    --timeout 60 \
    --max-instances 10 \
    --set-env-vars="GOOGLE_CLOUD_PROJECT=$PROJECT_ID"

# Get the service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format='value(status.url)')

echo ""
echo "✅ Deployment Complete!"
echo "======================"
echo ""
echo "🌐 Service URL: $SERVICE_URL"
echo ""
echo "🧪 Test Commands:"
echo ""
echo "# Health check:"
echo "curl $SERVICE_URL/health"
echo ""
echo "# Missed dose analysis:"
cat << 'EOF'
curl -X POST $SERVICE_URL/medications/missed-dose \
  -H "Content-Type: application/json" \
  -d '{
    "medication": "tacrolimus",
    "scheduled_time": "8:00 AM",
    "current_time": "2:00 PM",
    "patient_id": "maria_rodriguez"
  }'
EOF
echo ""
echo ""
echo "📊 Google Cloud Console:"
echo "https://console.cloud.google.com/run?project=$PROJECT_ID"
echo ""
echo "💡 To add Gemini API key:"
echo "gcloud run services update $SERVICE_NAME --set-env-vars GEMINI_API_KEY=your-key-here --region=$REGION"
echo ""
echo "🏆 Ready for Google Cloud Run Hackathon!"
