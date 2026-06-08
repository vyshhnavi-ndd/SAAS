from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class SignupRequest(BaseModel):
    tenant_name: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    tenant_id: str


class UserResponse(BaseModel):
    id: UUID
    email: str
    tenant_id: UUID
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TenantResponse(BaseModel):
    id: UUID
    name: str
    created_at: datetime
    max_documents: int

    class Config:
        from_attributes = True


class DocumentUploadRequest(BaseModel):
    filename: str
    size_bytes: int


class DocumentResponse(BaseModel):
    id: UUID
    original_filename: str
    document_size_bytes: int
    upload_date: datetime
    processed: bool
    metadata: dict

    class Config:
        from_attributes = True


class MessageRequest(BaseModel):
    content: str


class MessageResponse(BaseModel):
    id: UUID
    role: str
    content: str
    sources: List[dict]
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    id: UUID
    title: Optional[str]
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse] = []

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    conversation_id: Optional[str] = None
    message: str


class ChatResponse(BaseModel):
    conversation_id: str
    response: str
    sources: List[dict]
