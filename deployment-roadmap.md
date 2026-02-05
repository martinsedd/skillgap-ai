# SkillGap Deployment Roadmap - Phase 4

**Goal:** Secure, production-ready AWS deployment on free tier

**Priority Order:**
1. Get running in production (with security precautions)
2. Perfect CI/CD pipeline
3. Build frontend
4. Comprehensive testing

---

## Security-First Architecture

### Critical Assets to Protect
1. ✅ Database credentials (PostgreSQL)
2. ✅ API keys (Pinecone, Adzuna)
3. ✅ S3 access keys
4. ✅ Tailscale auth key
5. ✅ LLM endpoint (local machine IP - Tailscale only)

### Security Principles
- ✅ **No secrets in git** - Use .gitignore for all .env files
- ✅ **AWS SSM Parameter Store** - Encrypted secrets management
- ✅ **IAM roles for EC2** - No hardcoded AWS credentials
- ✅ **Security Groups** - Whitelist only necessary ports (80, 443, 22)
- ✅ **Encrypted at rest** - S3 encryption
- ✅ **Encrypted in transit** - HTTPS, Tailscale VPN
- ✅ **Least privilege** - IAM roles, minimal permissions
- ✅ **LLM isolation** - Local machine only, Tailscale tunnel

---

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         AWS Cloud (Free Tier)                    │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ EC2 t2.micro (1 vCPU, 1GB RAM) - FREE TIER                 │ │
│  │                                                             │ │
│  │  ├─ Docker: FastAPI Backend                                │ │
│  │  ├─ Docker: PostgreSQL (on same instance - FREE)           │ │
│  │  ├─ Tailscale Client (VPN to local LLM)                    │ │
│  │  └─ Nginx (reverse proxy for SSL)                          │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ S3 Bucket (Resume PDFs) - FREE TIER (5GB)                  │ │
│  │  ├─ Private bucket                                          │ │
│  │  ├─ Encrypted at rest (AES-256)                            │ │
│  │  └─ IAM role access only                                   │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ AWS Systems Manager Parameter Store                        │ │
│  │  ├─ /skillgap/prod/DATABASE_URL (encrypted)                │ │
│  │  ├─ /skillgap/prod/PINECONE_API_KEY (encrypted)            │ │
│  │  ├─ /skillgap/prod/ADZUNA_API_KEY (encrypted)              │ │
│  │  └─ /skillgap/prod/TAILSCALE_AUTH_KEY (encrypted)          │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │ Tailscale VPN
                              │ (encrypted tunnel)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Local Machine (Dev)                           │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ LLM Service (FastAPI + llama.cpp)                          │ │
│  │  ├─ Mistral-7B-Instruct-v0.3 Q5_K_M                        │ │
│  │  ├─ Exposed only via Tailscale (100.x.x.x:8001)            │ │
│  │  └─ NOT publicly accessible                                │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

External Services (Managed, Cloud):
- Pinecone (Vector DB) - FREE TIER
- Adzuna API - FREE TIER
- RemoteOK API - FREE
```

---

## Cost Breakdown (Target: $0/month)

| Service | Tier | Cost | Notes |
|---------|------|------|-------|
| EC2 t2.micro | Free | $0 | 750 hrs/month free tier |
| PostgreSQL | On EC2 | $0 | Run in Docker, no RDS |
| S3 (5GB) | Free | $0 | 5GB storage free tier |
| Data Transfer | Free | $0 | 100GB/month free tier |
| Pinecone | Free | $0 | 1 index, limited queries |
| Tailscale | Free | $0 | Personal use |
| **Total** | | **$0/month** | Stays in free tier |

---

## Phase 4 Implementation Steps

### ✅ Phase 4.0: Pre-Deployment Security Audit
- [ ] Create `.env.production.example` (template only, no secrets)
- [ ] Update `.gitignore` to block all .env files
- [ ] Document all required secrets
- [ ] Create secrets rotation strategy document

### ✅ Phase 4.1: Docker Configuration
- [ ] Create production Dockerfile for backend (multi-stage)
- [ ] Create docker-compose.yml for EC2 deployment
  - Backend service
  - PostgreSQL service
  - Nginx reverse proxy
- [ ] Add health check endpoints
- [ ] Configure restart policies
- [ ] Test locally with docker-compose

### ✅ Phase 4.2: AWS Infrastructure Setup (Manual First, Then Terraform)
- [ ] Create AWS account / Use existing
- [ ] Setup AWS CLI and credentials
- [ ] Create IAM role for EC2 (access to S3, SSM)
- [ ] Create S3 bucket for resumes (private, encrypted)
- [ ] Setup AWS SSM Parameter Store for secrets
- [ ] Launch EC2 t2.micro instance
- [ ] Configure security groups:
  - Inbound: 80 (HTTP), 443 (HTTPS), 22 (SSH - restricted IP)
  - Outbound: All (for API calls)

### ✅ Phase 4.3: EC2 Instance Configuration
- [ ] SSH into EC2 instance
- [ ] Install Docker and docker-compose
- [ ] Install Tailscale client
- [ ] Setup Tailscale connection to local LLM
- [ ] Pull secrets from AWS SSM Parameter Store
- [ ] Create .env file from SSM secrets (script)
- [ ] Clone repository
- [ ] Run docker-compose up -d
- [ ] Run database migrations (Alembic)
- [ ] Seed initial user data

### ✅ Phase 4.4: SSL & Domain Setup (Optional but Recommended)
- [ ] Get free domain (Freenom) or use existing
- [ ] Configure Route53 or Cloudflare DNS
- [ ] Setup Let's Encrypt SSL with Certbot
- [ ] Configure Nginx for HTTPS redirect

### ✅ Phase 4.5: Monitoring & Health Checks
- [ ] Setup CloudWatch logs (optional, costs may apply)
- [ ] Create health check endpoints (already have /health)
- [ ] Setup simple uptime monitoring (UptimeRobot - free)
- [ ] Create alerting for service downtime

### ✅ Phase 4.6: Terraform Infrastructure as Code
- [ ] Convert manual AWS setup to Terraform modules
  - `modules/compute/` - EC2 instance
  - `modules/storage/` - S3 bucket
  - `modules/security/` - IAM roles, security groups
- [ ] Create `terraform/environments/prod/` config
- [ ] Test terraform plan
- [ ] Document terraform deployment process

### ✅ Phase 4.7: GitHub Actions CI/CD Pipeline
- [ ] Create `.github/workflows/deploy.yml`
- [ ] Add GitHub Secrets:
  - AWS_ACCESS_KEY_ID
  - AWS_SECRET_ACCESS_KEY
  - EC2_SSH_KEY
  - EC2_HOST
- [ ] Pipeline stages:
  - Run tests (pytest)
  - Build Docker image
  - Push to Docker Hub
  - Deploy to EC2 via SSH
  - Run health checks
- [ ] Test deployment pipeline

### ✅ Phase 4.8: Documentation
- [ ] Update README.md with:
  - Architecture diagram
  - Deployment instructions
  - Environment variables guide
  - API documentation links
- [ ] Create DEPLOYMENT.md with step-by-step guide
- [ ] Document secret rotation procedures
- [ ] Create runbook for common issues

---

## Security Checklist (Before Going Live)

### Environment & Secrets
- [ ] No secrets in git history (`git log --all --full-history --source -- '*.env'`)
- [ ] All .env files in .gitignore
- [ ] AWS SSM Parameter Store configured with encryption
- [ ] IAM roles use least privilege principle
- [ ] Secrets rotation strategy documented

### Network Security
- [ ] Security groups restrict SSH to your IP only
- [ ] Only ports 80, 443, 22 open
- [ ] Tailscale configured for LLM access (no public exposure)
- [ ] S3 bucket is private (block public access enabled)
- [ ] HTTPS enabled with valid SSL certificate

### Application Security
- [ ] Authentication implemented (currently stub - document)
- [ ] Input validation with Pydantic (already done)
- [ ] Rate limiting on API endpoints (TODO: add)
- [ ] SQL injection protection (using SQLAlchemy ORM - safe)
- [ ] CORS configured correctly (restrict in production)

### Database Security
- [ ] PostgreSQL password is strong
- [ ] Database not publicly accessible (localhost only)
- [ ] Regular backups configured
- [ ] Connection pooling configured

### Monitoring
- [ ] Health check endpoint working
- [ ] Error logging configured (structlog)
- [ ] Uptime monitoring active
- [ ] Alert notifications configured

---

## Rollback Plan

If deployment fails or security issue discovered:

1. **Immediate Actions:**
   - Stop docker-compose services
   - Rotate all secrets in AWS SSM
   - Review CloudWatch logs for breach indicators

2. **Investigation:**
   - Check security group rules
   - Review IAM role permissions
   - Inspect application logs

3. **Recovery:**
   - Restore from known-good state
   - Update secrets
   - Re-deploy with fixes

---

## Post-Deployment Tasks

- [ ] Load test with realistic traffic (locust/k6)
- [ ] Test all API endpoints in production
- [ ] Verify Tailscale LLM connection
- [ ] Test job refresh scheduler (runs at 2 AM daily)
- [ ] Monitor costs in AWS console
- [ ] Setup billing alerts (alert at $5, $10, $15)
- [ ] Document any issues encountered
- [ ] Create operational runbook

---

## Future Enhancements (Post Phase 4)

- [ ] Replace StubAuthAdapter with real authentication (JWT/OAuth)
- [ ] Add rate limiting middleware
- [ ] Implement caching layer (Redis)
- [ ] Add comprehensive test suite
- [ ] Build React frontend
- [ ] Add API versioning
- [ ] Implement graceful shutdown
- [ ] Add database migrations automation
- [ ] Setup staging environment

---

## References

- AWS Free Tier: https://aws.amazon.com/free/
- Tailscale Setup: https://tailscale.com/kb/1017/install/
- Docker Compose Docs: https://docs.docker.com/compose/
- Terraform AWS Provider: https://registry.terraform.io/providers/hashicorp/aws/latest/docs
- GitHub Actions: https://docs.github.com/en/actions

---

**Current Status:** Phase 4.0 - Planning Complete
**Next Step:** Phase 4.0 - Pre-Deployment Security Audit
