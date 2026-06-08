from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.connection import AsyncSessionLocal
from app.database.rls import set_tenant_context
from app.utils.security import decode_token
import logging

logger = logging.getLogger(__name__)


class TenantContextMiddleware(BaseHTTPMiddleware):
    """Middleware that sets tenant context for RLS from JWT token."""

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request and set tenant context."""
        # Skip for public endpoints
        if request.url.path in ["/health", "/docs", "/openapi.json", "/redoc"]:
            return await call_next(request)

        if request.url.path.startswith("/api/v1/auth"):
            return await call_next(request)

        # Extract token from Authorization header
        auth_header = request.headers.get("authorization")

        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            payload = decode_token(token)

            if payload and "tenant_id" in payload:
                # Store tenant_id in request state for later use
                request.state.tenant_id = payload["tenant_id"]
                request.state.user_id = payload.get("sub")

                # Get a database session and set tenant context
                async with AsyncSessionLocal() as db:
                    try:
                        await set_tenant_context(db, payload["tenant_id"])
                    except Exception as e:
                        logger.error(f"Error setting tenant context: {str(e)}")

        return await call_next(request)
