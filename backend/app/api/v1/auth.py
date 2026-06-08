from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.models.schemas import SignupRequest, LoginRequest, TokenResponse
from app.services.auth_service import AuthService
from app.utils.errors import AuthenticationError, RagSaasException
from app.utils.logging import get_logger

router = APIRouter(prefix="/auth", tags=["auth"])
logger = get_logger(__name__)


@router.post("/signup", response_model=TokenResponse)
async def signup(request: SignupRequest, db: AsyncSession = Depends(get_db)):
    """Create a new tenant and user account."""
    try:
        return await AuthService.signup(request, db)
    except RagSaasException as e:
        logger.error(f"Signup error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in signup: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Signup failed",
        )


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate user and return JWT token."""
    try:
        return await AuthService.login(request, db)
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Login failed"
        )
