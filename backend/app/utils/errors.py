class RagSaasException(Exception):
    """Base exception for RAG SaaS."""
    pass


class AuthenticationError(RagSaasException):
    """Authentication failed."""
    pass


class AuthorizationError(RagSaasException):
    """User not authorized for this action."""
    pass


class TenantNotFoundError(RagSaasException):
    """Tenant not found."""
    pass


class UserNotFoundError(RagSaasException):
    """User not found."""
    pass


class DocumentNotFoundError(RagSaasException):
    """Document not found."""
    pass


class ConversationNotFoundError(RagSaasException):
    """Conversation not found."""
    pass


class VectorDatabaseError(RagSaasException):
    """Vector database error."""
    pass


class InvalidTokenError(AuthenticationError):
    """Token is invalid or expired."""
    pass
