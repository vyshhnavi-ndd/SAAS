from fastapi import APIRouter

router = APIRouter(prefix="/chat", tags=["chat"])


@router.get("/conversations")
async def list_conversations():
    """List conversations for current user."""
    return {"message": "Not implemented yet"}


@router.post("/conversations")
async def create_conversation():
    """Create a new conversation."""
    return {"message": "Not implemented yet"}


@router.post("/message")
async def send_message():
    """Send a chat message."""
    return {"message": "Not implemented yet"}
