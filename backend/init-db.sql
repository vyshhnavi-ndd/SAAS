-- Initialize database with RLS policies

-- Enable RLS on all tables
ALTER DATABASE ragdb SET app.current_tenant_id TO '';

-- Create documents table with RLS
CREATE TABLE IF NOT EXISTS tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    api_key_hash VARCHAR(255) NOT NULL UNIQUE,
    vector_db_collection_name TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    max_documents INT DEFAULT 1000
);

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tenant_id, email)
);

CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    original_filename VARCHAR(255) NOT NULL,
    storage_path TEXT NOT NULL,
    document_size_bytes INT,
    uploaded_by UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed BOOLEAN DEFAULT FALSE,
    metadata JSONB DEFAULT '{}',
    UNIQUE(tenant_id, storage_path)
);

CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(10) NOT NULL,
    content TEXT NOT NULL,
    sources JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Enable RLS
ALTER TABLE tenants ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;

-- RLS Policies for documents (tenant isolation)
CREATE POLICY documents_tenant_isolation ON documents
    FOR SELECT
    USING (tenant_id = (current_setting('app.current_tenant_id'))::uuid);

CREATE POLICY documents_tenant_insert ON documents
    FOR INSERT
    WITH CHECK (tenant_id = (current_setting('app.current_tenant_id'))::uuid);

CREATE POLICY documents_tenant_update ON documents
    FOR UPDATE
    USING (tenant_id = (current_setting('app.current_tenant_id'))::uuid);

-- RLS Policies for users
CREATE POLICY users_tenant_isolation ON users
    FOR SELECT
    USING (tenant_id = (current_setting('app.current_tenant_id'))::uuid);

CREATE POLICY users_tenant_insert ON users
    FOR INSERT
    WITH CHECK (tenant_id = (current_setting('app.current_tenant_id'))::uuid);

-- RLS Policies for conversations
CREATE POLICY conversations_tenant_isolation ON conversations
    FOR SELECT
    USING (tenant_id = (current_setting('app.current_tenant_id'))::uuid);

CREATE POLICY conversations_tenant_insert ON conversations
    FOR INSERT
    WITH CHECK (tenant_id = (current_setting('app.current_tenant_id'))::uuid);

-- RLS Policies for messages
CREATE POLICY messages_tenant_isolation ON messages
    FOR SELECT
    USING (tenant_id = (current_setting('app.current_tenant_id'))::uuid);

CREATE POLICY messages_tenant_insert ON messages
    FOR INSERT
    WITH CHECK (tenant_id = (current_setting('app.current_tenant_id'))::uuid);
