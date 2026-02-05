# Secrets Management

## Required Secrets for Production

### Database

- `DATABASE_URL` - PostgreSQL connection string
  - Format: `postgresql://user:password@localhost:5432/skillgap`
  - Generated: Strong password (20+ chars, alphanumeric + symbols)

### Pinecone Vector DB

- `PINECONE_API_KEY` - From Pinecone dashboard
- `PINECONE_INDEX_NAME` - Index name (create in Pinecone)
- `PINECONE_ENVIRONMENT` - Region (e.g., us-west1-gcp)

### Job APIS

- `ADZUNA_APP_ID` - From Adzuna developer portal
- `ADZUNA_API_KEY` - From Adzuna developer portal

### AWS

- IAM role attached to EC2 (no keys needed in .env)
- S3 bucket name: `skillgap-resumes-prod`

### Tailscale

- `TAILSCALE_AUTH_KEY` - From Tailscale admin console
- Used during EC2 setup, not in .env

### LLM Endpoint

- `LLM_ENDPOINT` - Tailscale IP of local machine
  - Format: `http://100.x.x.x:8001`
  - Obtained after Tailscale setup

## Storage in AWS

All secrets stored in AWS Systems Manager Parameter Store:

- Path: `/skillgap/prod/{SECRET_NAME}`
- Encryption: KMS encrypted
- Access: EC2 IAM role only
