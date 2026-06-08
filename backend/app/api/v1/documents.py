from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.middleware.auth import get_current_user
from app.models.schemas import DocumentResponse
from app.services.document_service import document_service
from app.utils.errors import RagSaasException, DocumentNotFoundError
from app.utils.logging import get_logger

router = APIRouter(prefix="/documents", tags=["documents"])
logger = get_logger(__name__)

# Max file size: 50MB
MAX_FILE_SIZE = 50 * 1024 * 1024


@router.get("/", response_model=list[DocumentResponse])
async def list_documents(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all documents for current tenant."""
    try:
        documents = await document_service.list_documents(
            current_user["tenant_id"], db
        )
        return documents
    except RagSaasException as e:
        logger.error(f"Error listing documents: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error listing documents: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list documents",
        )


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a document."""
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="No filename provided"
            )

        # Check file size
        file_content = await file.read()
        if len(file_content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large (max {MAX_FILE_SIZE / 1024 / 1024:.0f}MB)",
            )

        # Validate file type
        valid_extensions = {".pdf", ".txt", ".docx"}
        file_ext = f".{file.filename.split('.')[-1].lower()}" if "." in file.filename else ""
        if file_ext not in valid_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. Supported: {', '.join(valid_extensions)}",
            )

        # Upload document
        document = await document_service.upload_document(
            file_content=file_content,
            filename=file.filename,
            tenant_id=current_user["tenant_id"],
            user_id=current_user["user_id"],
            db=db,
        )

        # TODO: Queue async task to process document (chunk, embed, store in Weaviate)
        # For now, just return the uploaded document
        logger.info(f"Document uploaded: {document.id}")

        return document

    except HTTPException:
        raise
    except RagSaasException as e:
        logger.error(f"Error uploading document: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error uploading document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload document",
        )
    finally:
        await file.close()


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific document."""
    try:
        document = await document_service.get_document(document_id, db)

        # Verify ownership
        if str(document.tenant_id) != current_user["tenant_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot access other tenants' documents",
            )

        return document
    except DocumentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get document",
        )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a document."""
    try:
        await document_service.delete_document(document_id, current_user["tenant_id"], db)
    except DocumentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(e)
        )
    except RagSaasException as e:
        logger.error(f"Error deleting document: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error deleting document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document",
        )
