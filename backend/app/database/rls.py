from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text


async def set_tenant_context(session: AsyncSession, tenant_id: str) -> None:
    """
    Set the tenant context for RLS.
    This must be called at the start of each request for a tenant.
    """
    await session.execute(
        text("SET app.current_tenant_id = :tenant_id"),
        {"tenant_id": tenant_id}
    )


async def clear_tenant_context(session: AsyncSession) -> None:
    """Clear the tenant context."""
    await session.execute(text("RESET app.current_tenant_id"))
