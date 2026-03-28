#!/bin/bash

# Deploy HMDA RAG Agent to Cloud Run

PROJECT_ID="tourgemini"
REGION="europe-west1"
SERVICE_NAME="hmda-rag-agent"
IMAGE_NAME="hmda-rag-agent"

echo "🚀 Deploying HMDA RAG Agent to Cloud Run"
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Service: $SERVICE_NAME"

# Step 1: Build Docker image
echo -e "\n1️⃣  Building Docker image..."
docker build -t $IMAGE_NAME:latest .

# Step 2: Tag for GCP
echo -e "\n2️⃣  Tagging image for GCP..."
docker tag $IMAGE_NAME:latest gcr.io/$PROJECT_ID/$IMAGE_NAME:latest

# Step 3: Push to GCP Artifact Registry
echo -e "\n3️⃣  Pushing to Artifact Registry..."
docker push gcr.io/$PROJECT_ID/$IMAGE_NAME:latest

# Step 4: Deploy to Cloud Run
echo -e "\n4️⃣  Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$IMAGE_NAME:latest \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory 4Gi \
  --timeout 300 \
  --project $PROJECT_ID

echo -e "\n✅ Deployment complete!"
echo "Service URL:"
gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)' --project $PROJECT_ID
