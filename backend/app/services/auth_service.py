from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select
from uuid import UUID
from datetime import timedelta

from app.models.db import Tenant, User
from app.models.schemas import SignupRequest, LoginRequest, TokenResponse
from app.utils.security import hash_password, verify_password, create_access_token
from app.utils.errors import AuthenticationError, UserNotFoundError, TenantNotFoundError
from app.utils.logging import get_logger
from app.services.tenant_service import tenant_service

logger = get_logger(__name__)


class AuthService:
    @staticmethod
    async def signup(request: SignupRequest, db: AsyncSession) -> TokenResponse:
        """
        Create a new tenant and user account.
        Returns JWT token for immediate login.
        """
        try:
            # Create tenant with Weaviate collection
            tenant = await tenant_service.create_tenant(request.tenant_name, db)

            # Create user
            user = User(
                tenant_id=tenant.id,
                email=request.email,
                password_hash=hash_password(request.password),
                is_admin=True,  # First user is admin
                is_active=True,
            )
            db.add(user)
            await db.commit()

            # Generate token
            access_token = create_access_token(
                data={"sub": str(user.id), "tenant_id": str(tenant.id)}
            )

            logger.info(f"New signup: tenant={tenant.id}, user={user.id}")

            return TokenResponse(
                access_token=access_token,
                user_id=str(user.id),
                tenant_id=str(tenant.id),
            )

        except Exception as e:
            logger.error(f"Signup error: {str(e)}")
            await db.rollback()
            raise

    @staticmethod
    async def login(request: LoginRequest, db: AsyncSession) -> TokenResponse:
        """
        Authenticate user and return JWT token.
        """
        try:
            # Find user by email (search across all tenants)
            result = await db.execute(
                select(User).where(User.email == request.email)
            )
            user = result.scalar_one_or_none()

            if user is None:
                raise AuthenticationError("Invalid email or password")

            # Verify password
            if not verify_password(request.password, user.password_hash):
                raise AuthenticationError("Invalid email or password")

            if not user.is_active:
                raise AuthenticationError("User account is inactive")

            # Generate token
            access_token = create_access_token(
                data={"sub": str(user.id), "tenant_id": str(user.tenant_id)}
            )

            logger.info(f"User login: user={user.id}, tenant={user.tenant_id}")

            return TokenResponse(
                access_token=access_token,
                user_id=str(user.id),
                tenant_id=str(user.tenant_id),
            )

        except AuthenticationError:
            raise
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            raise AuthenticationError("Authentication failed")

    @staticmethod
    async def get_user_by_id(user_id: UUID, db: AsyncSession) -> User:
        """Get user by ID."""
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if user is None:
            raise UserNotFoundError(f"User {user_id} not found")

        return user

    @staticmethod
    async def get_tenant_by_id(tenant_id: UUID, db: AsyncSession) -> Tenant:
        """Get tenant by ID."""
        result = await db.execute(
            select(Tenant).where(Tenant.id == tenant_id)
        )
        tenant = result.scalar_one_or_none()

        if tenant is None:
            raise TenantNotFoundError(f"Tenant {tenant_id} not found")

        return tenant