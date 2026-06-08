from sqlalchemy import Column, String, DateTime, Integer, Boolean, ForeignKey, JSON, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid

from app.database.connection import Base


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    api_key_hash = Column(String(255), nullable=False, unique=True)
    vector_db_collection_name = Column(String(255), nullable=False, unique=True)
    created_at = Column(DateTime, server_default=func.now())
    max_documents = Column(Integer, default=1000)

    users = relationship("User", back_populates="tenant")
    documents = relationship("Document", back_populates="tenant")
    conversations = relationship("Conversation", back_populates="tenant")


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    email = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())

    tenant = relationship("Tenant", back_populates="users")
    conversations = relationship("Conversation", back_populates="user")
    messages = relationship("Message", back_populates="user")

    __table_args__ = (UniqueConstraint("tenant_id", "email"),)


class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    original_filename = Column(String(255), nullable=False)
    storage_path = Column(Text, nullable=False)
    document_size_bytes = Column(Integer)
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    upload_date = Column(DateTime, server_default=func.now())
    processed = Column(Boolean, default=False)
    metadata = Column(JSON, default={})

    tenant = relationship("Tenant", back_populates="documents")

    __table_args__ = (UniqueConstraint("tenant_id", "storage_path"),)


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String(255))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    tenant = relationship("Tenant", back_populates="conversations")
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation")


class Message(Base):
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    role = Column(String(10), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    sources = Column(JSON, default=[])  # Array of source documents
    created_at = Column(DateTime, server_default=func.now())

    conversation = relationship("Conversation", back_populates="messages")
    tenant = relationship("Tenant")
    user = relationship("User", back_populates="messages")
