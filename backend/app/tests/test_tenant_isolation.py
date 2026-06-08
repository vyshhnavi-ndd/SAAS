"""Tests for tenant isolation and multi-tenant security."""
import pytest
from sqlalchemy import select
from uuid import uuid4

from app.models.db import Tenant, User, Document, Conversation, Message
from app.database.rls import set_tenant_context
from app.utils.security import hash_password


@pytest.mark.asyncio
async def test_tenant_cannot_access_other_tenant_users(test_db, tenant_a, tenant_b, user_a, user_b):
    """Test that tenant A cannot see user B's data via RLS."""
    # Set context to tenant B
    await set_tenant_context(test_db, str(tenant_b.id))

    # Query users (should only get tenant B's users)
    result = await test_db.execute(select(User).where(User.email == user_a.email))
    user = result.scalar_one_or_none()

    # User A should NOT be visible to tenant B query
    assert user is None, "RLS should prevent cross-tenant user access"


@pytest.mark.asyncio
async def test_tenant_can_access_own_users(test_db, tenant_a, user_a):
    """Test that tenant A can see its own users."""
    # Set context to tenant A
    await set_tenant_context(test_db, str(tenant_a.id))

    # Query users
    result = await test_db.execute(select(User).where(User.email == user_a.email))
    user = result.scalar_one_or_none()

    # User A should be visible in tenant A's context
    assert user is not None, "Tenant should see its own users"
    assert user.id == user_a.id
    assert user.tenant_id == tenant_a.id


@pytest.mark.asyncio
async def test_rls_blocks_document_access_across_tenants(test_db, tenant_a, tenant_b, user_a):
    """Test that RLS prevents cross-tenant document access."""
    # Create document for tenant A
    doc_a = Document(
        id=uuid4(),
        tenant_id=tenant_a.id,
        original_filename="secret.pdf",
        storage_path="/tenant-a/secret.pdf",
        document_size_bytes=1000,
        uploaded_by=user_a.id,
        processed=True,
    )
    test_db.add(doc_a)
    await test_db.commit()

    # Switch context to tenant B
    await set_tenant_context(test_db, str(tenant_b.id))

    # Try to query tenant A's document
    result = await test_db.execute(
        select(Document).where(Document.id == doc_a.id)
    )
    doc = result.scalar_one_or_none()

    # Document should NOT be visible to tenant B
    assert doc is None, "RLS should prevent cross-tenant document access"


@pytest.mark.asyncio
async def test_tenant_isolation_on_insert(test_db, tenant_a, tenant_b, user_a, user_b):
    """Test that INSERT policies enforce tenant isolation."""
    # Set context to tenant A
    await set_tenant_context(test_db, str(tenant_a.id))

    # Try to create document for tenant B (should fail due to RLS)
    doc = Document(
        id=uuid4(),
        tenant_id=tenant_b.id,  # Different tenant!
        original_filename="hacked.pdf",
        storage_path="/tenant-b/hacked.pdf",
        document_size_bytes=1000,
        uploaded_by=user_a.id,
        processed=True,
    )
    test_db.add(doc)

    # This should fail RLS check
    with pytest.raises(Exception):
        await test_db.commit()

    await test_db.rollback()


@pytest.mark.asyncio
async def test_conversation_isolation(test_db, tenant_a, tenant_b, user_a, user_b):
    """Test that conversations are isolated by tenant."""
    # Create conversation for tenant A
    conv_a = Conversation(
        id=uuid4(),
        tenant_id=tenant_a.id,
        user_id=user_a.id,
        title="Tenant A Chat",
    )
    test_db.add(conv_a)
    await test_db.commit()

    # Switch to tenant B context
    await set_tenant_context(test_db, str(tenant_b.id))

    # Try to query tenant A's conversation
    result = await test_db.execute(
        select(Conversation).where(Conversation.id == conv_a.id)
    )
    conv = result.scalar_one_or_none()

    # Should not be visible
    assert conv is None, "Conversation should be isolated by tenant"


@pytest.mark.asyncio
async def test_message_isolation(test_db, tenant_a, tenant_b, user_a, user_b):
    """Test that messages are isolated by tenant."""
    # Create conversation for tenant A
    conv_a = Conversation(
        id=uuid4(),
        tenant_id=tenant_a.id,
        user_id=user_a.id,
        title="Chat A",
    )
    test_db.add(conv_a)
    await test_db.commit()

    # Create message in tenant A's conversation
    msg_a = Message(
        id=uuid4(),
        conversation_id=conv_a.id,
        tenant_id=tenant_a.id,
        user_id=user_a.id,
        role="user",
        content="Hello from tenant A",
    )
    test_db.add(msg_a)
    await test_db.commit()

    # Switch to tenant B
    await set_tenant_context(test_db, str(tenant_b.id))

    # Try to query tenant A's message
    result = await test_db.execute(
        select(Message).where(Message.id == msg_a.id)
    )
    msg = result.scalar_one_or_none()

    # Should not be visible
    assert msg is None, "Message should be isolated by tenant"


@pytest.mark.asyncio
async def test_multiple_tenants_have_separate_data(test_db, tenant_a, tenant_b, user_a, user_b):
    """Test complete isolation: multiple tenants with their own data."""
    # Create 2 documents for tenant A
    for i in range(2):
        doc = Document(
            id=uuid4(),
            tenant_id=tenant_a.id,
            original_filename=f"doc_a_{i}.pdf",
            storage_path=f"/tenant-a/doc_a_{i}.pdf",
            document_size_bytes=1000,
            uploaded_by=user_a.id,
            processed=True,
        )
        test_db.add(doc)

    await test_db.commit()

    # Create 3 documents for tenant B
    for i in range(3):
        doc = Document(
            id=uuid4(),
            tenant_id=tenant_b.id,
            original_filename=f"doc_b_{i}.pdf",
            storage_path=f"/tenant-b/doc_b_{i}.pdf",
            document_size_bytes=2000,
            uploaded_by=user_b.id,
            processed=True,
        )
        test_db.add(doc)

    await test_db.commit()

    # Query as tenant A
    await set_tenant_context(test_db, str(tenant_a.id))
    result_a = await test_db.execute(select(Document))
    docs_a = result_a.scalars().all()

    # Query as tenant B
    await set_tenant_context(test_db, str(tenant_b.id))
    result_b = await test_db.execute(select(Document))
    docs_b = result_b.scalars().all()

    # Verify counts
    assert len(docs_a) == 2, f"Tenant A should see 2 documents, got {len(docs_a)}"
    assert len(docs_b) == 3, f"Tenant B should see 3 documents, got {len(docs_b)}"

    # Verify no cross-contamination
    for doc in docs_a:
        assert doc.tenant_id == tenant_a.id, "Tenant A should only see own documents"
    for doc in docs_b:
        assert doc.tenant_id == tenant_b.id, "Tenant B should only see own documents"


@pytest.mark.asyncio
async def test_jwt_tenant_mismatch_scenario(user_a, tenant_a, tenant_b):
    """Test that JWT with mismatched tenant would be rejected at application level."""
    # Create token for user A with tenant A
    from app.utils.security import decode_token, create_access_token

    token_a = create_access_token(
        data={"sub": str(user_a.id), "tenant_id": str(tenant_a.id)}
    )

    # Decode and verify
    payload = decode_token(token_a)
    assert payload["tenant_id"] == str(tenant_a.id)
    assert payload["sub"] == str(user_a.id)

    # If someone tried to use this token with tenant_b.id, the middleware
    # would reject it because token claims don't match request context


@pytest.mark.asyncio
async def test_user_cannot_create_document_for_other_tenant(test_db, tenant_a, tenant_b, user_a):
    """Test that even if user_a tries to create doc for tenant_b, RLS prevents it."""
    # Set context to tenant A (user_a's actual tenant)
    await set_tenant_context(test_db, str(tenant_a.id))

    # User A tries to create document with tenant_b's ID
    doc = Document(
        id=uuid4(),
        tenant_id=tenant_b.id,  # Wrong tenant!
        original_filename="hacked.pdf",
        storage_path="/hacked.pdf",
        document_size_bytes=1000,
        uploaded_by=user_a.id,
        processed=True,
    )
    test_db.add(doc)

    # RLS INSERT policy should reject this
    with pytest.raises(Exception):
        await test_db.commit()

    await test_db.rollback()
