from alembic.config import Config
from alembic import command
import os
import sys

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

def migrate_database():
    """Run database migrations using Alembic"""
    # Get database directory
    db_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Create Alembic configuration
    alembic_cfg = Config()
    alembic_cfg.set_main_option('script_location', os.path.join(db_dir, 'alembic'))
    alembic_cfg.set_main_option('sqlalchemy.url', f'sqlite:///{os.path.join(db_dir, "tenants.db")}')
    
    try:
        # Run migrations
        command.upgrade(alembic_cfg, "head")
        print("Database migrated successfully!")
    except Exception as e:
        print(f"Error during migration: {str(e)}")

if __name__ == "__main__":
    migrate_database()
