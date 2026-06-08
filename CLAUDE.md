# RAG SaaS - Project Documentation

## Overview

Multitenant SaaS platform for document-based RAG (Retrieval-Augmented Generation). Users upload documents, ask questions, and get AI-powered answers with source citations.

**Tech Stack:** FastAPI + React + PostgreSQL + Weaviate, deployed on AWS free tier.

## Architecture

### Multi-Tenancy Model
- **Database Level**: PostgreSQL Row-Level Security (RLS) - each query filtered by tenant_id
- **Application Level**: JWT tokens contain tenant_id claim, set via middleware
- **Vector DB Level**: Tenant-per-collection in Weaviate

### Key Design Decisions

1. **RLS as primary isolation**: Database enforces tenant isolation, application code is secondary defense
2. **JWT with tenant claims**: Simplifies auth flow, tenant_id always in token
3. **Local embeddings (MVP)**: sentence-transformers runs locally (free), can upgrade to Azure OpenAI later
4. **Ollama for LLM**: Self-hosted (free), scales well, can upgrade to managed service

## Development Setup

### Start local dev environment
```bash
docker-compose up -d
docker exec rag-saas-ollama ollama pull llama2:7b
```

### Services
- Backend: http://localhost:8000 (FastAPI)
- Frontend: http://localhost:5173 (React)
- Weaviate: http://localhost:8080
- PostgreSQL: localhost:5432 (user: postgres, pass: postgres)

### Environment Files
- `backend/.env.example` → `backend/.env`
- `frontend/.env.example` → `frontend/.env`

## Key Files

### Backend
- `backend/app/main.py` - FastAPI application entry
- `backend/app/models/db.py` - ORM models (Tenant, User, Document, etc.)
- `backend/app/services/auth_service.py` - Signup/login logic
- `backend/init-db.sql` - Database schema with RLS policies
- `backend/app/database/rls.py` - Tenant context management

### Frontend
- `frontend/src/App.tsx` - Main React app with routing
- `frontend/src/context/AuthContext.tsx` - Auth state management
- `frontend/src/services/api.ts` - Axios client with token injection
- `frontend/src/pages/LoginPage.tsx` - Signup/login UI

## Database Schema

### Tables
- `tenants` - Tenant metadata
- `users` - User accounts (unique per tenant)
- `documents` - Uploaded documents
- `conversations` - Chat sessions
- `messages` - Chat messages with sources

### Row-Level Security (RLS)
All tables have RLS enabled. Queries automatically filtered by `app.current_tenant_id` setting.

Example:
```python
# Set tenant context at start of request
await set_tenant_context(db, user_tenant_id)
# All queries now return only this tenant's data
users = await db.execute(select(User))  # Filtered by RLS
```

## API Design

### Authentication Flow
1. POST `/api/v1/auth/signup` - Create tenant + user
2. Returns JWT with `tenant_id` and `user_id` claims
3. Frontend stores token, includes in all requests
4. Backend validates token, extracts tenant_id, sets RLS context

### Protected Endpoints
All endpoints (except `/health`, `/auth/*`) require `Authorization: Bearer {token}` header.

## Phases Status

- ✅ **Phase 1**: Project Setup - Directory structure, Docker Compose, basic API/UI
- 🔄 **Phase 2**: Database & Multi-Tenant - RLS policies, tenant isolation tests
- ⏳ **Phase 3**: Authentication - Signup/login endpoints (skeleton ready)
- ⏳ **Phase 4**: Tenant Management - Admin endpoints for tenant creation
- ⏳ **Phase 5**: Document Management - Upload, chunking, embedding pipeline
- ⏳ **Phase 6**: Frontend - Dashboard, document UI, API integration
- ⏳ **Phase 7**: Chat & RAG - Vector search, LLM integration
- ⏳ **Phase 8**: Integration Testing - E2E tests, isolation verification

## Common Tasks

### Run tests
```bash
cd backend
pytest -v
pytest app/tests/test_tenant_isolation.py -v  # Tenant isolation tests
```

### Add a new API endpoint
1. Create route in `backend/app/api/v1/{feature}.py`
2. Add service logic in `backend/app/services/{feature}_service.py`
3. Add Pydantic schemas in `backend/app/models/schemas.py`
4. Include router in `backend/app/main.py`

### Add a frontend page
1. Create component in `frontend/src/pages/`
2. Add route in `frontend/src/App.tsx`
3. Add API calls in `frontend/src/services/`

## Deployment (AWS Free Tier)

### Initial setup
- EC2 t2.micro for backend
- RDS PostgreSQL db.t2.micro
- S3 for document storage
- CloudFront for frontend CDN

**Costs**: $0/month for 12 months (free tier), then ~$50-100/month for minimal load.

### CI/CD
- GitHub Actions for tests
- Push to AWS ECR for backend
- Deploy via Terraform

## Tenant Isolation Verification

Always run isolation tests before deploying:

```python
# Test 1: RLS blocks cross-tenant access
async def test_tenant_cannot_access_other_tenant_docs():
    tenant_a = await create_tenant("Company A")
    tenant_b = await create_tenant("Company B")
    doc_a = await create_document(tenant_a.id, "secret.pdf")
    
    await set_tenant_context(db, tenant_b.id)
    results = await db.execute(select(Document).where(Document.id == doc_a.id))
    assert results.scalar() is None  # Tenant B cannot see A's docs

# Test 2: JWT with mismatched tenant is rejected
async def test_jwt_tenant_mismatch_rejected():
    token_for_a = create_jwt(tenant_id=tenant_a.id, user_id=user_a.id)
    response = client.post(
        "/api/v1/chat/message",
        headers={"Authorization": f"Bearer {token_for_a}"},
        json={"conversation_id": tenant_b_conversation_id}
    )
    assert response.status_code == 403
```

## Notes for Future Implementation

1. **Embeddings**: Replace sentence-transformers with Azure OpenAI API when budget allows
2. **LLM**: Upgrade from Ollama to Azure OpenAI or other managed service for production
3. **Scaling**: Move from single EC2 to Kubernetes (ECS/AKS) when needed
4. **Monitoring**: Add Application Insights / DataDog for production observability
5. **Auth**: Consider Auth0 migration if advanced features (MFA, SSO) needed
6. **Storage**: Integrate AWS S3 for document storage (currently local)

## Troubleshooting

### Services not starting
```bash
docker-compose logs -f <service-name>
docker-compose down -v && docker-compose up
```

### Database connection errors
```bash
# Check PostgreSQL is running
docker-compose ps postgres
# Connect directly
psql postgresql://postgres:postgres@localhost:5432/ragdb
```

### Weaviate not ready
```bash
# Check status
curl http://localhost:8080/v1/.well-known/ready
```

### Frontend can't reach backend
Check `VITE_API_URL` in `frontend/.env` matches backend URL (http://localhost:8000 for dev)
