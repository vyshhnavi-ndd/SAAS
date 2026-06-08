# RAG SaaS Backend API

FastAPI-based backend for multitenant RAG platform with PostgreSQL Row-Level Security.

## Development

### Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Create .env from example
cp .env.example .env

# Run with Docker Compose (recommended)
docker-compose up -d
```

### Database

```bash
# Run migrations
python -m alembic upgrade head

# Or use manage.py
python manage.py upgrade

# Create new migration
python -m alembic revision --autogenerate -m "Description"
```

### Testing

```bash
# Run all tests
pytest -v

# Run specific test file
pytest app/tests/test_auth.py -v

# Run tests with coverage
pytest --cov=app app/tests/
```

## API Endpoints

### Authentication (Public)

#### Signup
```http
POST /api/v1/auth/signup
Content-Type: application/json

{
  "tenant_name": "Acme Corp",
  "email": "user@acme.com",
  "password": "securepass123"
}

Response: 200 OK
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "tenant_id": "550e8400-e29b-41d4-a716-446655440001"
}
```

#### Login
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@acme.com",
  "password": "securepass123"
}

Response: 200 OK
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "user_id": "...",
  "tenant_id": "..."
}
```

### Health (Public)
```http
GET /health

Response: 200 OK
{
  "status": "ok"
}
```

### Tenants (Protected)

#### List Tenants
```http
GET /api/v1/tenants
Authorization: Bearer {token}

Response: 200 OK
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "name": "Acme Corp",
    "created_at": "2026-06-08T10:00:00",
    "max_documents": 1000
  }
]
```

#### Get Tenant
```http
GET /api/v1/tenants/{tenant_id}
Authorization: Bearer {token}

Response: 200 OK
{
  "id": "...",
  "name": "Acme Corp",
  "created_at": "...",
  "max_documents": 1000
}
```

## Authentication

All protected endpoints require a JWT token in the `Authorization` header:

```
Authorization: Bearer {access_token}
```

Token claims:
- `sub`: User ID
- `tenant_id`: Tenant ID (used for RLS)
- `exp`: Expiration time (24 hours)

## Multi-Tenant Isolation

### Database Level (RLS)
All tables have Row-Level Security enabled. Queries are automatically filtered by tenant_id:

```sql
SELECT * FROM documents;  -- Returns only current tenant's documents
```

### Application Level
- Middleware extracts tenant_id from JWT token
- RLS context is set for all requests: `SET app.current_tenant_id = {tenant_id}`
- All SQL queries are automatically filtered

### API Level
- Protected endpoints require valid JWT token
- Token must include valid tenant_id
- Cross-tenant access is rejected

## Error Responses

### 401 Unauthorized
```json
{
  "detail": "Invalid or expired token"
}
```

### 403 Forbidden
```json
{
  "detail": "Cannot access other tenants"
}
```

### 422 Unprocessable Entity (Validation)
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "invalid email format",
      "type": "value_error.email"
    }
  ]
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

## Architecture

### Request Flow
```
1. Client POST /signup
2. Backend creates Tenant (in DB)
3. Backend creates Weaviate collection (for vectors)
4. Backend creates User (in DB with tenant_id)
5. Backend generates JWT with {user_id, tenant_id}
6. Client stores token in localStorage
7. Client includes token in all subsequent requests
8. Middleware extracts tenant_id and sets RLS context
9. All queries filtered by tenant_id automatically
```

### Directory Structure
```
app/
├── main.py              # FastAPI app entry
├── config.py            # Configuration
├── middleware/
│   ├── auth.py          # JWT validation
│   └── tenant_context.py # RLS context setup
├── api/v1/
│   ├── auth.py          # Auth endpoints
│   ├── tenants.py       # Tenant endpoints
│   ├── documents.py     # Document endpoints
│   └── chat.py          # Chat endpoints
├── models/
│   ├── db.py            # ORM models
│   └── schemas.py       # Pydantic schemas
├── services/
│   ├── auth_service.py
│   └── tenant_service.py
├── database/
│   ├── connection.py
│   ├── rls.py
│   └── migrations/      # Alembic migrations
├── utils/
│   ├── security.py      # JWT + password hashing
│   ├── errors.py        # Custom exceptions
│   └── logging.py
└── tests/
    ├── conftest.py      # Pytest fixtures
    ├── test_auth.py
    └── test_tenant_isolation.py
```

## Configuration

Environment variables (see `.env.example`):

| Variable | Default | Purpose |
|----------|---------|---------|
| `DATABASE_URL` | PostgreSQL | Async connection string |
| `JWT_SECRET_KEY` | dev-key | JWT signing key (change in production!) |
| `JWT_EXPIRATION_HOURS` | 24 | Token lifetime |
| `WEAVIATE_URL` | http://localhost:8080 | Vector DB |
| `OLLAMA_BASE_URL` | http://localhost:11434 | Local LLM |
| `EMBEDDING_MODEL` | all-MiniLM-L6-v2 | Embeddings model |

## Deployment

### Docker
```bash
docker-compose up -d

# Migrations run automatically on startup
```

### AWS (Production)
```bash
# Build image
docker build -t rag-saas:latest .

# Push to ECR
aws ecr get-login-password | docker login --username AWS --password-stdin {account}.dkr.ecr.us-east-1.amazonaws.com
docker tag rag-saas:latest {account}.dkr.ecr.us-east-1.amazonaws.com/rag-saas:latest
docker push {account}.dkr.ecr.us-east-1.amazonaws.com/rag-saas:latest

# Deploy to ECS/EC2
```

## Performance Notes

- RLS policies are enforced at the database level (fastest)
- JWT tokens cached in request state (no repeated decoding)
- Async database queries (non-blocking)
- Connection pooling via SQLAlchemy

## Security

- ✅ Passwords hashed with bcrypt
- ✅ JWT tokens signed and validated
- ✅ RLS prevents cross-tenant access at database level
- ✅ CORS configured for frontend
- ✅ SQL injection prevention via ORM
- ⏳ Rate limiting (to implement)
- ⏳ API key rotation (to implement)

## Troubleshooting

### Database Connection Error
```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check logs
docker-compose logs postgres
```

### Weaviate Connection Error
```bash
# Check Weaviate status
curl http://localhost:8080/v1/.well-known/ready

# Check logs
docker-compose logs weaviate
```

### Migration Issues
```bash
# Current migration status
python manage.py current

# Downgrade last migration
python manage.py downgrade

# See all migrations
python manage.py history
```

## Contributing

1. Create a new branch: `git checkout -b feature/my-feature`
2. Write tests in `app/tests/`
3. Follow black code style: `black app/`
4. Run tests: `pytest -v`
5. Push and create PR

## License

MIT
