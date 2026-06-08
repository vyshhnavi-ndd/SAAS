from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID, uuid4
import weaviate
from app.models.db import Tenant
from app.config import settings
from app.utils.errors import TenantNotFoundError
from app.utils.logging import get_logger

logger = get_logger(__name__)


class TenantService:
    def __init__(self):
        self.weaviate_client = weaviate.Client(settings.WEAVIATE_URL)

    async def create_tenant(self, name: str, db: AsyncSession) -> Tenant:
        """
        Create a new tenant and initialize Weaviate collection.
        """
        try:
            # Generate collection name
            collection_name = f"documents_{name.lower().replace(' ', '_')}_{uuid.uuid4().hex[:8]}"

            # Create tenant in database
            tenant = Tenant(
                name=name,
                api_key_hash="temp",  # Will be updated with actual API key in future
                vector_db_collection_name=collection_name,
                max_documents=1000,
            )
            db.add(tenant)
            await db.flush()

            # Create Weaviate collection for this tenant
            self._create_weaviate_collection(collection_name)

            await db.commit()
            await db.refresh(tenant)

            logger.info(f"Created tenant: {tenant.id} with collection {collection_name}")
            return tenant

        except Exception as e:
            logger.error(f"Error creating tenant: {str(e)}")
            await db.rollback()
            raise

    def _create_weaviate_collection(self, collection_name: str) -> None:
        """Create a Weaviate collection for a tenant."""
        try:
            # Check if collection already exists
            if self.weaviate_client.schema.exists(collection_name):
                logger.info(f"Collection {collection_name} already exists")
                return

            # Create collection
            self.weaviate_client.schema.create_class(
                {
                    "class": collection_name,
                    "properties": [
                        {"name": "content", "dataType": ["text"]},
                        {"name": "source", "dataType": ["text"]},
                        {"name": "document_id", "dataType": ["text"]},
                        {"name": "chunk_index", "dataType": ["int"]},
                        {"name": "metadata", "dataType": ["object"]},
                    ],
                    "vectorizer": "none",  # We'll provide embeddings manually
                }
            )

            logger.info(f"Created Weaviate collection: {collection_name}")

        except Exception as e:
            logger.error(f"Error creating Weaviate collection: {str(e)}")
            raise

    async def get_tenant_by_id(self, tenant_id: UUID, db: AsyncSession) -> Tenant:
        """Get tenant by ID."""
        result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
        tenant = result.scalar_one_or_none()

        if not tenant:
            raise TenantNotFoundError(f"Tenant {tenant_id} not found")

        return tenant

    async def list_tenants(self, db: AsyncSession) -> list[Tenant]:
        """List all tenants (admin only)."""
        result = await db.execute(select(Tenant))
        return result.scalars().all()

    async def delete_tenant(self, tenant_id: UUID, db: AsyncSession) -> None:
        """Delete a tenant and its Weaviate collection."""
        try:
            tenant = await self.get_tenant_by_id(tenant_id, db)

            # Delete Weaviate collection
            if self.weaviate_client.schema.exists(tenant.vector_db_collection_name):
                self.weaviate_client.schema.delete_class(
                    tenant.vector_db_collection_name
                )

            # Delete from database (cascade deletes related records)
            await db.delete(tenant)
            await db.commit()

            logger.info(f"Deleted tenant: {tenant_id}")

        except Exception as e:
            logger.error(f"Error deleting tenant: {str(e)}")
            await db.rollback()
            raise


# Create singleton instance
tenant_service = TenantService()
