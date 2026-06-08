from fastapi import APIRouter

router = APIRouter(prefix="/tenants", tags=["tenants"])


@router.get("/")
async def list_tenants():
    """List all tenants (admin only)."""
    return {"message": "Not implemented yet"}


@router.post("/")
async def create_tenant():
    """Create a new tenant (admin only)."""
    return {"message": "Not implemented yet"}
