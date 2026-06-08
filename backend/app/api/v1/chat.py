from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.database.connection import get_db
from app.middleware.auth import get_current_user
from app.models.schemas import ConversationResponse, MessageRequest, ChatResponse
from app.services.chat_service import chat_service
from app.utils.errors import RagSaasException, ConversationNotFoundError
from app.utils.logging import get_logger

router = APIRouter(prefix="/chat", tags=["chat"])
logger = get_logger(__name__)


@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
    title: str = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new conversation."""
    try:
        conversation = await chat_service.create_conversation(
            tenant_id=current_user["tenant_id"],
            user_id=current_user["user_id"],
            title=title,
            db=db,
        )
        return conversation
    except RagSaasException as e:
        logger.error(f"Error creating conversation: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error creating conversation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create conversation",
        )


@router.get("/conversations", response_model=list[ConversationResponse])
async def list_conversations(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all conversations for current user's tenant."""
    try:
        conversations = await chat_service.list_conversations(
            tenant_id=current_user["tenant_id"],
            db=db,
        )
        return conversations
    except RagSaasException as e:
        logger.error(f"Error listing conversations: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error listing conversations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list conversations",
        )


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific conversation."""
    try:
        conversation = await chat_service.get_conversation(conversation_id, db)

        # Verify ownership
        if str(conversation.tenant_id) != current_user["tenant_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot access other tenants' conversations",
            )

        return conversation
    except ConversationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting conversation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get conversation",
        )


@router.post("/conversations/{conversation_id}/messages", response_model=ChatResponse)
async def send_message(
    conversation_id: str,
    request: MessageRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send a message and get AI response."""
    try:
        # Verify conversation ownership
        conversation = await chat_service.get_conversation(conversation_id, db)
        if str(conversation.tenant_id) != current_user["tenant_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot access other tenants' conversations",
            )

        # Get AI response
        answer, sources = await chat_service.answer_question(
            conversation_id=conversation_id,
            tenant_id=current_user["tenant_id"],
            user_id=current_user["user_id"],
            question=request.content,
            db=db,
        )

        return ChatResponse(
            conversation_id=conversation_id,
            response=answer,
            sources=sources,
        )

    except ConversationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found"
        )
    except HTTPException:
        raise
    except RagSaasException as e:
        logger.error(f"Error sending message: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error sending message: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process message",
        )


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a conversation."""
    try:
        await chat_service.delete_conversation(
            conversation_id=conversation_id,
            tenant_id=current_user["tenant_id"],
            db=db,
        )
    except ConversationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(e)
        )
    except RagSaasException as e:
        logger.error(f"Error deleting conversation: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error deleting conversation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete conversation",
        )
