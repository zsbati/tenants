from .database import DatabaseManager
from ..models.tenant import Base
import os
import shutil
import datetime

def migrate_database():
    manager = DatabaseManager()
    
    # Get database paths
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tenants.db')
    backup_path = db_path + '.backup'
    
    # Check if database exists
    if os.path.exists(db_path):
        try:
            # Try to create a backup
            shutil.copy2(db_path, backup_path)
            print(f"Created backup at {backup_path}")
            
            # Remove existing database
            os.remove(db_path)
            print("Removed existing database")
        except Exception as e:
            print(f"Warning: Could not create backup: {str(e)}")
            print("Continuing with migration...")
    
    # Create new database with updated schema
    manager.initialize_database()
    print("Database migrated successfully!")

if __name__ == "__main__":
    migrate_database()
