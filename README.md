# SkillGap

An AI-powered job search assistant that uses semantic matching and agentic workflows to help candidates identify
skill gaps and practice mock interviews.

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![React](https://img.shields.io/badge/react-%2320232b.svg?style=for-the-badge&logo=react&logoColor=%2361DAFB)
![Terraform](https://img.shields.io/badge/terraform-%235835CC.svg?style=for-the-badge&logo=terraform&logoColor=white)
![Tailscale](https://img.shields.io/badge/tailscale-990000?style=for-the-badge&logo=tailscale&logoColor=white)
![AWS](https://img.shields.io/badge/AWS-%23FF9900.svg?style=for-the-badge&logo=amazon-aws&logoColor=white)

## Engineering Highlights

- Hexagonal Architecture (Ports & Adapters): Decoupled domain logic from infrastructure, allowing easy swapping of
  LLM providers and data sources.
- Local LLM Inference via Tailscale: Optimized cost and privacy by running Mistral-7B on local hardware while serving
  a cloud-hosted API through a secure Tailscale tunnel.
- Agentic Interview: Built with LangGraph, implementing a state-machine-based interview agent that generates questions
  based on specific resume-job skill gaps.
- Semantic Search: Utilizes Pinecone and `allmpnet-base-v2` embeddings for high-accuracy job matching beyond simple
  keyword filtering.

## Tech Stack

- Backend: FastAPI, SQLAlchemy, Alembic, APScheduler, Structlog.
- AI/ML: Mistral-7B (llama.cpp), LangGraph, Pinecone, SentenceTransformers.
- Frontend: React, Vite, Tailwind CSS, shadcn/ui, TanStack Query.
- DevOps/Infra: Terraform, Docker, Github Actions, Tailscale.

## System Architecture

The project follows Domain-Driven Design (DDD) principles to ensure long-term maintainability:

```text
[ Cloud: AWS ]                                      [Local Environment]
      |                                                      |
    FastAPI App <--- Secure Tailscape Tunnel ---> LLM Service (Mistral-7B)
    PostgreSQL                                    llama.cpp (ROCm GPU)
    Pinecone DB
```

- Domain Layer: Pure Pythn models and services (Job matching, Gap analysis).
- Adapters:
  - `LocalLLMAdapter`: Interfaces with the tunneled LLM service.
  - `VectorDBPort`: Handles vector upserts and similarity searches in Pinecone.
  - `JobSourcePort`: Aggregates data from Adzuna and RemoteOK APIs.
- Infrastructure: Automated daily job refreshes via APScheduler and deduplication using SHA256 hashing.

## Project Status

SkillGap is currently in **Active Development (Phase 4)**. The core engine, domain logic, and AI integrations are fully
functional, with the final focus on infrastructure automation and the frontend interface.

| Module              | Status      | Technical Notes                                      |
| :------------------ | :---------- | :--------------------------------------------------- |
| **Domain Logic **   | Complete    | Hexagonal core, repositories, and matching services  |
| **AI Integration ** | Complete    | LangGraph state machine & Local LLM tunneling        |
| **Backend API**     | Complete    | FastAPI endpoints, JSON logging, & deduplication     |
| **Infrastructure**  | In Progress | Migrating local Compose to Terraform/AWS (Debugging) |
| **Frontend UI**     | Pending     | React + shadcn/ui demo dashboard implementation      |
| **Test Suite**      | Pending     | Expanding domain unit tests to full E2E coverage     |

### Current Sprint: Deployment & Demo

- **Terraform**: Resolving VPC/Security Group orchestration issues on AWS.
- **Frontend**: Initializing React/Vite project and mapping API schema to UI components.
- **Testing**: Implementing `pytest` fixtures for the LangGraph agent state transitions.

---

Eduardo Martins - Feb 2026
