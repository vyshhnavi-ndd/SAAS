"""Initial migration: Create tables with RLS policies

Revision ID: 001_initial_schema
Revises:
Create Date: 2026-06-08 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create tenants table
    op.create_table(
        'tenants',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('api_key_hash', sa.String(255), nullable=False),
        sa.Column('vector_db_collection_name', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.Column('max_documents', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('api_key_hash'),
        sa.UniqueConstraint('vector_db_collection_name')
    )

    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_admin', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'email')
    )

    # Create documents table
    op.create_table(
        'documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('original_filename', sa.String(255), nullable=False),
        sa.Column('storage_path', sa.Text(), nullable=False),
        sa.Column('document_size_bytes', sa.Integer(), nullable=True),
        sa.Column('uploaded_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('upload_date', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.Column('processed', sa.Boolean(), nullable=True),
        sa.Column('metadata', postgresql.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'storage_path')
    )

    # Create conversations table
    op.create_table(
        'conversations',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create messages table
    op.create_table(
        'messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.String(10), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('sources', postgresql.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Enable RLS on all tables
    op.execute('ALTER TABLE tenants ENABLE ROW LEVEL SECURITY;')
    op.execute('ALTER TABLE users ENABLE ROW LEVEL SECURITY;')
    op.execute('ALTER TABLE documents ENABLE ROW LEVEL SECURITY;')
    op.execute('ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;')
    op.execute('ALTER TABLE messages ENABLE ROW LEVEL SECURITY;')

    # Create RLS policies for documents
    op.execute('''
        CREATE POLICY documents_tenant_isolation ON documents
        FOR SELECT
        USING (tenant_id = (current_setting('app.current_tenant_id'))::uuid);
    ''')

    op.execute('''
        CREATE POLICY documents_tenant_insert ON documents
        FOR INSERT
        WITH CHECK (tenant_id = (current_setting('app.current_tenant_id'))::uuid);
    ''')

    op.execute('''
        CREATE POLICY documents_tenant_update ON documents
        FOR UPDATE
        USING (tenant_id = (current_setting('app.current_tenant_id'))::uuid);
    ''')

    # Create RLS policies for users
    op.execute('''
        CREATE POLICY users_tenant_isolation ON users
        FOR SELECT
        USING (tenant_id = (current_setting('app.current_tenant_id'))::uuid);
    ''')

    op.execute('''
        CREATE POLICY users_tenant_insert ON users
        FOR INSERT
        WITH CHECK (tenant_id = (current_setting('app.current_tenant_id'))::uuid);
    ''')

    # Create RLS policies for conversations
    op.execute('''
        CREATE POLICY conversations_tenant_isolation ON conversations
        FOR SELECT
        USING (tenant_id = (current_setting('app.current_tenant_id'))::uuid);
    ''')

    op.execute('''
        CREATE POLICY conversations_tenant_insert ON conversations
        FOR INSERT
        WITH CHECK (tenant_id = (current_setting('app.current_tenant_id'))::uuid);
    ''')

    # Create RLS policies for messages
    op.execute('''
        CREATE POLICY messages_tenant_isolation ON messages
        FOR SELECT
        USING (tenant_id = (current_setting('app.current_tenant_id'))::uuid);
    ''')

    op.execute('''
        CREATE POLICY messages_tenant_insert ON messages
        FOR INSERT
        WITH CHECK (tenant_id = (current_setting('app.current_tenant_id'))::uuid);
    ''')


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('messages')
    op.drop_table('conversations')
    op.drop_table('documents')
    op.drop_table('users')
    op.drop_table('tenants')
