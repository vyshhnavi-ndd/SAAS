#!/usr/bin/env python
"""Database management script."""
import sys
import asyncio
from alembic.config import Config
from alembic import command
from app.database.connection import init_db, close_db
from app.config import settings


def setup_alembic_config():
    """Set up Alembic configuration."""
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
    return alembic_cfg


def migrate_upgrade():
    """Run pending migrations."""
    alembic_cfg = setup_alembic_config()
    command.upgrade(alembic_cfg, "head")
    print("✓ Database upgraded to latest migration")


def migrate_downgrade():
    """Rollback the last migration."""
    alembic_cfg = setup_alembic_config()
    command.downgrade(alembic_cfg, "-1")
    print("✓ Database downgraded")


def migrate_current():
    """Show current migration revision."""
    alembic_cfg = setup_alembic_config()
    command.current(alembic_cfg)


def migrate_history():
    """Show migration history."""
    alembic_cfg = setup_alembic_config()
    command.history(alembic_cfg)


def init_database():
    """Initialize database (create tables without migrations)."""
    asyncio.run(init_db())
    print("✓ Database initialized")


async def close_database():
    """Close database connections."""
    await close_db()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python manage.py [command]")
        print()
        print("Commands:")
        print("  upgrade       Run pending migrations")
        print("  downgrade     Rollback the last migration")
        print("  current       Show current migration revision")
        print("  history       Show migration history")
        print("  init          Initialize database (create tables)")
        sys.exit(1)

    command = sys.argv[1]

    if command == "upgrade":
        migrate_upgrade()
    elif command == "downgrade":
        migrate_downgrade()
    elif command == "current":
        migrate_current()
    elif command == "history":
        migrate_history()
    elif command == "init":
        init_database()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
