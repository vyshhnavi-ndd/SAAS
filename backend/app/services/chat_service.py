"""Chat service for RAG-powered conversations."""
from typing import List, Dict, Any, Tuple
from uuid import UUID
import weaviate
import requests

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.db import Conversation, Message, Document, Tenant
from app.services.document_service import EmbeddingGenerator
from app.config import settings
from app.utils.errors import ConversationNotFoundError, VectorDatabaseError
from app.utils.logging import get_logger

logger = get_logger(__name__)


class RAGEngine:
    """Retrieval-Augmented Generation engine."""

    def __init__(self):
        self.weaviate_client = weaviate.Client(settings.WEAVIATE_URL)
        self.embedder = EmbeddingGenerator()
        self.llm_base_url = settings.OLLAMA_BASE_URL

    async def search_documents(
        self,
        query: str,
        tenant_id: UUID,
        collection_name: str,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """Search for relevant document chunks using vector similarity."""
        try:
            # Generate embedding for query
            query_embedding = self.embedder.embed(query)

            # Search Weaviate
            result = self.weaviate_client.query.get(
                collection_name,
                ["content", "source", "document_id", "chunk_index"],
            ).with_near_vector({
                "vector": query_embedding
            }).with_limit(top_k).do()

            # Extract results
            chunks = result.get("data", {}).get("Get", {}).get(collection_name, [])

            logger.info(
                f"Found {len(chunks)} relevant chunks for tenant {tenant_id}"
            )

            return chunks

        except Exception as e:
            logger.error(f"Error searching documents: {str(e)}")
            raise VectorDatabaseError(f"Vector search failed: {str(e)}")

    def build_rag_prompt(
        self,
        query: str,
        context_chunks: List[Dict[str, Any]],
    ) -> str:
        """Build RAG prompt with context."""
        # Format context
        context_text = "\n\n".join(
            [
                f"[From: {chunk.get('source', 'Unknown')}]\n{chunk.get('content', '')}"
                for chunk in context_chunks
            ]
        )

        # Build prompt
        prompt = f"""You are a helpful AI assistant. Answer the user's question based on the provided context.
If the answer is not in the context, say "I don't have enough information to answer this question."
Always cite the source document when providing information.

CONTEXT:
{context_text if context_text else "No relevant documents found."}

QUESTION: {query}

ANSWER:"""

        return prompt

    def call_llm(self, prompt: str) -> str:
        """Call local LLM (Ollama) to generate response."""
        try:
            response = requests.post(
                f"{self.llm_base_url}/api/generate",
                json={
                    "model": settings.OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                },
                timeout=30,
            )

            if response.status_code != 200:
                raise Exception(f"LLM error: {response.text}")

            result = response.json()
            return result.get("response", "").strip()

        except requests.exceptions.ConnectionError:
            logger.error(f"Cannot connect to Ollama at {self.llm_base_url}")
            raise VectorDatabaseError(
                f"LLM service unavailable. Make sure Ollama is running at {self.llm_base_url}"
            )
        except Exception as e:
            logger.error(f"Error calling LLM: {str(e)}")
            raise VectorDatabaseError(f"LLM call failed: {str(e)}")

    async def answer_question(
        self,
        query: str,
        tenant_id: UUID,
        collection_name: str,
        top_k: int = 5,
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """Answer a question using RAG pipeline."""
        try:
            # Search for relevant documents
            chunks = await self.search_documents(
                query, tenant_id, collection_name, top_k
            )

            # Build RAG prompt
            prompt = self.build_rag_prompt(query, chunks)

            # Call LLM
            answer = self.call_llm(prompt)

            return answer, chunks

        except Exception as e:
            logger.error(f"Error in RAG pipeline: {str(e)}")
            raise


class ChatService:
    """Service for conversation management."""

    def __init__(self):
        self.rag_engine = RAGEngine()

    async def create_conversation(
        self,
        tenant_id: UUID,
        user_id: UUID,
        title: str = None,
        db: AsyncSession = None,
    ) -> Conversation:
        """Create a new conversation."""
        try:
            conversation = Conversation(
                tenant_id=tenant_id,
                user_id=user_id,
                title=title or "New Chat",
            )

            db.add(conversation)
            await db.commit()
            await db.refresh(conversation)

            logger.info(f"Created conversation {conversation.id} for user {user_id}")

            return conversation

        except Exception as e:
            logger.error(f"Error creating conversation: {str(e)}")
            await db.rollback()
            raise

    async def get_conversation(
        self,
        conversation_id: UUID,
        db: AsyncSession,
    ) -> Conversation:
        """Get a conversation with its messages."""
        try:
            result = await db.execute(
                select(Conversation).where(Conversation.id == conversation_id)
            )
            conversation = result.scalar_one_or_none()

            if not conversation:
                raise ConversationNotFoundError(
                    f"Conversation {conversation_id} not found"
                )

            return conversation

        except ConversationNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error getting conversation: {str(e)}")
            raise

    async def list_conversations(
        self,
        tenant_id: UUID,
        db: AsyncSession,
    ) -> List[Conversation]:
        """List all conversations for a tenant."""
        try:
            result = await db.execute(
                select(Conversation)
                .where(Conversation.tenant_id == tenant_id)
                .order_by(Conversation.updated_at.desc())
            )
            return result.scalars().all()

        except Exception as e:
            logger.error(f"Error listing conversations: {str(e)}")
            raise

    async def add_message(
        self,
        conversation_id: UUID,
        tenant_id: UUID,
        user_id: UUID,
        role: str,
        content: str,
        sources: List[Dict[str, Any]] = None,
        db: AsyncSession = None,
    ) -> Message:
        """Add a message to a conversation."""
        try:
            message = Message(
                conversation_id=conversation_id,
                tenant_id=tenant_id,
                user_id=user_id,
                role=role,
                content=content,
                sources=sources or [],
            )

            db.add(message)
            await db.commit()
            await db.refresh(message)

            return message

        except Exception as e:
            logger.error(f"Error adding message: {str(e)}")
            await db.rollback()
            raise

    async def answer_question(
        self,
        conversation_id: UUID,
        tenant_id: UUID,
        user_id: UUID,
        question: str,
        db: AsyncSession,
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """Answer a user's question using RAG."""
        try:
            # Get tenant to find Weaviate collection
            result = await db.execute(select(Conversation).where(Conversation.id == conversation_id))
            conversation = result.scalar_one_or_none()

            if not conversation:
                raise ConversationNotFoundError(f"Conversation {conversation_id} not found")

            # Get tenant's Weaviate collection
            tenant_result = await db.execute(
                select(Conversation.tenant)
            )
            # Reload to get relationship
            conversation = await self.get_conversation(conversation_id, db)

            # Use RAG to answer
            answer, chunks = await self.rag_engine.answer_question(
                query=question,
                tenant_id=tenant_id,
                collection_name=conversation.tenant.vector_db_collection_name,
                top_k=5,
            )

            # Format sources
            sources = [
                {
                    "document_id": chunk.get("document_id"),
                    "source": chunk.get("source"),
                    "chunk_index": chunk.get("chunk_index"),
                }
                for chunk in chunks
            ]

            # Store messages
            await self.add_message(
                conversation_id=conversation_id,
                tenant_id=tenant_id,
                user_id=user_id,
                role="user",
                content=question,
                sources=[],  # User message has no sources
                db=db,
            )

            await self.add_message(
                conversation_id=conversation_id,
                tenant_id=tenant_id,
                user_id=user_id,
                role="assistant",
                content=answer,
                sources=sources,
                db=db,
            )

            return answer, sources

        except Exception as e:
            logger.error(f"Error answering question: {str(e)}")
            raise

    async def delete_conversation(
        self,
        conversation_id: UUID,
        tenant_id: UUID,
        db: AsyncSession,
    ) -> None:
        """Delete a conversation and its messages."""
        try:
            conversation = await self.get_conversation(conversation_id, db)

            # Verify ownership
            if conversation.tenant_id != tenant_id:
                raise ValueError("Conversation does not belong to this tenant")

            # Delete all messages (cascade will handle this)
            await db.delete(conversation)
            await db.commit()

            logger.info(f"Deleted conversation {conversation_id}")

        except Exception as e:
            logger.error(f"Error deleting conversation: {str(e)}")
            await db.rollback()
            raise


# Create singleton instance
chat_service = ChatService()
