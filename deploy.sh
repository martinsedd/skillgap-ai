#!/bin/bash
set -e

echo "Starting SkillGap deployment..."

#############################################################| Secret Loading |##########################################################################
export POSTGRES_USER=$(aws ssm get-parameter --name "/skillgap/prod/POSTGRES_USER" --with-decryption --query 'Parameter.Value' --output text)
export POSTGRES_PASSWORD=$(aws ssm get-parameter --name "/skillgap/prod/POSTGRES_PASSWORD" --with-decryption --query 'Parameter.Value' --output text)
#########################################################################################################################################################
export PINECONE_API_KEY=$(aws ssm get-parameter --name "/skillgap/prod/PINECONE_API_KEY" --with-decryption --query 'Parameter.Value' --output text)
export PINECONE_INDEX_NAME=$(aws ssm get-parameter --name "/skillgap/prod/PINECONE_INDEX_NAME" --with-decryption --query 'Parameter.Value' --output text)
export PINECONE_ENVIRONMENT=$(aws ssm get-parameter --name "/skillgap/prod/PINECONE_ENVIRONMENT" --with-decryption --query 'Parameter.Value' --output text)
#########################################################################################################################################################
export ADZUNA_APP_ID=$(aws ssm get-parameter --name "/skillgap/prod/ADZUNA_APP_ID" --with-decryption --query 'Parameter.Value' --output text)
export ADZUNA_API_KEY=$(aws ssm get-parameter --name "/skillgap/prod/ADZUNA_API_KEY" --with-decryption --query 'Parameter.Value' --output text)
export ADZUNA_COUNTRY=$(aws ssm get-parameter --name "/skillgap/prod/ADZUNA_COUNTRY" --with-decryption --query 'Parameter.Value' --output text)
#########################################################################################################################################################
export LLM_ENDPOINT=$(aws ssm get-parameter --name "/skillgap/prod/LLM_ENDPOINT" --with-decryption --query 'Parameter.Value' --output text)
#########################################################################################################################################################
export STORAGE_BUCKET=$(aws ssm get-parameter --name "/skillgap/prod/STORAGE_BUCKET" --with-decryption --query 'Parameter.Value' --output text)
#############################################################| Defaults |################################################################################
export REMOTEOK_API_URL="https://remoteok.com/api"
export EMBEDDING_MODEL="sentence-transformers/all-mpnet-base-v2"
export AUTH_STUB_USER_ID="default-user"
export JOB_REFRESH_CRON="0 2 * * *"
export STORAGE_PROVIDER="s3"
export AWS_REGION="ca-central-1"
export LOG_LEVEL="INFO"
#########################################################################################################################################################
echo "Secrets loaded"
#############################################################| Containerization |########################################################################
# Pull latest code
echo "Pulling latest code..."
git pull origin main
# Build and start containers
echo "Building Docker images..."
docker-compose -f docker-compose.prod.yml build --no-cache
echo "Starting containers"
docker-compose -f docker-compose.prod.yml up -d
#############################################################| Database Prep |###########################################################################
# Wait for database to be ready
echo "Waiting for database..."
sleep 10
# Run migrations
echo "Running database migrations..."
docker-compose -f docker-compose.prod.yml exec -T backend alembic upgrade head
#############################################################| Double Checking... |######################################################################
# Health check
echo "Running health check..."
sleep 5
if curl -f http://localhost/health; then
  echo "Deployment successful!"
else
  echo "Health check failed!"
  exit 1
fi
#############################################################| That actually worked, eh?! |##############################################################
echo "SkillGap is running!"
