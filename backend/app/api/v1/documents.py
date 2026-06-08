from fastapi import APIRouter

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("/")
async def list_documents():
    """List documents for current tenant."""
    return {"message": "Not implemented yet"}


@router.post("/upload")
async def upload_document():
    """Upload a document."""
    return {"message": "Not implemented yet"}
