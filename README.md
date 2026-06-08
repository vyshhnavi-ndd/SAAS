# RAG SaaS - Multitenant Document Q&A Platform

A production-ready multitenant SaaS application for document-based retrieval-augmented generation (RAG) using FastAPI, React, PostgreSQL, and Weaviate.

## Features

- **Multitenant Architecture**: Complete data isolation using PostgreSQL Row-Level Security (RLS)
- **JWT Authentication**: Secure user authentication and authorization
- **Document Management**: Upload, chunk, and embed documents
- **Vector Search**: Fast semantic search using Weaviate
- **RAG Chat**: Ask questions about documents and get AI-powered answers
- **Tenant Isolation**: Bulletproof isolation at database, application, and vector DB levels

## Tech Stack

### Backend
- **FastAPI**: High-performance Python web framework
- **PostgreSQL**: Relational database with RLS support
- **SQLAlchemy**: Async ORM
- **Weaviate**: Vector database for embeddings
- **Sentence-Transformers**: Local embeddings generation

### Frontend
- **React 18**: UI library
- **TypeScript**: Type-safe JavaScript
- **Vite**: Fast build tool
- **Axios**: HTTP client

### Deployment
- **Docker & Docker Compose**: Containerization and orchestration
- **AWS Free Tier**: PostgreSQL (RDS), EC2, S3, CloudFront (future)

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 18+ (for local frontend development)
- Python 3.11+ (for local backend development)

### Local Development

1. **Clone the repository**
```bash
git clone <repo-url>
cd Multitenant-saas/SAAS
```

2. **Start all services**
```bash
docker-compose up -d
```

3. **Pull Ollama model** (first time only)
```bash
docker exec rag-saas-ollama ollama pull llama2:7b
```

4. **Services available at**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - Weaviate: http://localhost:8080
   - PostgreSQL: localhost:5432

### Creating First User

Visit http://localhost:5173 and click "Sign Up" to create your first tenant and user account.

## Project Structure

```
Multitenant-saas/SAAS/
├── backend/              # FastAPI application
├── frontend/             # React + TypeScript application
├── docker-compose.yml    # Local development stack
├── .gitignore
└── README.md
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/signup` - Create tenant and user
- `POST /api/v1/auth/login` - Login user

### Documents
- `GET /api/v1/documents` - List documents
- `POST /api/v1/documents/upload` - Upload document

### Chat
- `GET /api/v1/chat/conversations` - List conversations
- `POST /api/v1/chat/conversations` - Create conversation
- `POST /api/v1/chat/message` - Send message

## Environment Variables

### Backend (.env)
See `backend/.env.example`

### Frontend (.env)
See `frontend/.env.example`

## Testing

Run tests:
```bash
cd backend
pytest -v
```

Test tenant isolation:
```bash
pytest app/tests/test_tenant_isolation.py -v
```

## Deployment

### AWS Deployment
1. Push backend Docker image to AWS ECR
2. Deploy to EC2 t2.micro (free tier)
3. Set up RDS PostgreSQL (free tier)
4. Deploy frontend to S3 + CloudFront

See deployment docs for detailed instructions.

## Development Phases

- [x] Phase 1: Project Setup
- [ ] Phase 2: Database & Multi-Tenant Foundation
- [ ] Phase 3: Authentication
- [ ] Phase 4: Tenant Management
- [ ] Phase 5: Document Management
- [ ] Phase 6: Frontend Setup
- [ ] Phase 7: Chat & RAG
- [ ] Phase 8: Integration & Testing

## License

MIT

## Support

For issues and questions, please use GitHub Issues.
