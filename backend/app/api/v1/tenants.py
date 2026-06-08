from fastapi import APIRouter, HTTPException, status, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.middleware.auth import get_current_user
from app.models.schemas import TenantResponse
from app.services.tenant_service import tenant_service
from app.utils.errors import RagSaasException
from app.utils.logging import get_logger

router = APIRouter(prefix="/tenants", tags=["tenants"])
logger = get_logger(__name__)


@router.get("/", response_model=list[TenantResponse])
async def list_tenants(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all tenants (admin only - currently just returns current tenant)."""
    try:
        # For now, just return the current tenant
        # In production, add admin role checks here
        tenant = await tenant_service.get_tenant_by_id(current_user["tenant_id"], db)
        return [tenant]
    except RagSaasException as e:
        logger.error(f"Error listing tenants: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in list_tenants: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list tenants",
        )


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific tenant (must be current user's tenant)."""
    try:
        # Verify user owns this tenant
        if current_user["tenant_id"] != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot access other tenants",
            )

        tenant = await tenant_service.get_tenant_by_id(tenant_id, db)
        return tenant
    except RagSaasException as e:
        logger.error(f"Error getting tenant: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in get_tenant: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get tenant",
        )

