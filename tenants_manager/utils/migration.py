import logging
from alembic import command
from alembic.config import Config
from pathlib import Path
import os
import sys

from ..config.database import get_migrations_dir

# Configure logger for this module
logger = logging.getLogger(__name__)

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


def migrate_database():
    """Run database migrations using Alembic"""
    # Get database directory
    db_dir = get_migrations_dir()

    # Create Alembic configuration
    alembic_cfg = Config()
    alembic_cfg.set_main_option("script_location", os.path.join(db_dir, "alembic"))
    alembic_cfg.set_main_option(
        "sqlalchemy.url", f'sqlite:///{os.path.join(db_dir, "tenants.db")}'
    )

    try:
        # Run migrations
        command.upgrade(alembic_cfg, "head")
        logger.info("Database migrated successfully")
    except Exception as e:
        logger.error(f"Error during migration: {str(e)}")


if __name__ == "__main__":
    migrate_database()
