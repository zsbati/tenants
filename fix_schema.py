"""
Script to manually update the database schema to match the models.
This is a one-time script to fix the database schema.
"""
import os
import sys
import sqlite3
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

# Import the database URL function
from tenants_manager.config.database import get_database_url

def main():
    # Get the database URL
    db_url = get_database_url()
    db_path = db_url.replace('sqlite:///', '')
    
    print(f"Updating database schema: {db_path}")
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if room_id column already exists
        cursor.execute("PRAGMA table_info(tenants)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Add room_id column if it doesn't exist
        if 'room_id' not in columns:
            print("Adding room_id column to tenants table...")
            cursor.execute("""
                ALTER TABLE tenants 
                ADD COLUMN room_id INTEGER 
                REFERENCES rooms(id)
            """)
            print("✓ Added room_id column")
        else:
            print("✓ room_id column already exists")
        
        # Make room_id non-nullable after data migration
        # First, ensure all tenants have a room_id
        cursor.execute("""
            SELECT COUNT(*) 
            FROM tenants 
            WHERE room_id IS NULL AND room IS NOT NULL
        """)
        null_room_count = cursor.fetchone()[0]
        
        if null_room_count > 0:
            print(f"Found {null_room_count} tenants with room but no room_id")
            print("Creating rooms and setting room_id...")
            
            # Get all unique room names
            cursor.execute("SELECT DISTINCT room FROM tenants WHERE room IS NOT NULL")
            room_names = [row[0] for row in cursor.fetchall()]
            
            # Create rooms and get their IDs
            room_ids = {}
            for room_name in room_names:
                cursor.execute(
                    "INSERT OR IGNORE INTO rooms (name, capacity) VALUES (?, ?)",
                    (room_name, 1)  # Default capacity of 1
                )
                cursor.execute("SELECT id FROM rooms WHERE name = ?", (room_name,))
                room_id = cursor.fetchone()[0]
                room_ids[room_name] = room_id
                
                # Update tenants with this room name
                cursor.execute(
                    "UPDATE tenants SET room_id = ? WHERE room = ?",
                    (room_id, room_name)
                )
            
            print(f"✓ Created {len(room_ids)} rooms and updated tenant room references")
        
        # Make room_id non-nullable
        print("Making room_id non-nullable...")
        
        # SQLite doesn't support ALTER COLUMN to change nullability, so we need to recreate the table
        cursor.execute("PRAGMA foreign_keys=off")
        
        # Create a new table with the correct schema
        cursor.execute("""
            CREATE TABLE tenants_new (
                id INTEGER NOT NULL,
                name VARCHAR(100) NOT NULL,
                room_id INTEGER NOT NULL,
                rent FLOAT NOT NULL,
                bi VARCHAR(20) NOT NULL,
                email VARCHAR(100),
                phone VARCHAR(20),
                address VARCHAR(200),
                birth_date DATE NOT NULL,
                entry_date DATE NOT NULL,
                created_at DATETIME,
                updated_at DATETIME,
                is_active BOOLEAN DEFAULT '1' NOT NULL,
                deleted_at DATETIME,
                PRIMARY KEY (id),
                UNIQUE (bi),
                FOREIGN KEY(room_id) REFERENCES rooms (id)
            )
        """)
        
        # Copy data from old table to new table
        cursor.execute("""
            INSERT INTO tenants_new (
                id, name, room_id, rent, bi, email, phone, address,
                birth_date, entry_date, created_at, updated_at, is_active, deleted_at
            )
            SELECT 
                id, name, room_id, rent, bi, email, phone, address,
                birth_date, entry_date, created_at, updated_at, is_active, deleted_at
            FROM tenants
        """)
        
        # Drop the old table and rename the new one
        cursor.execute("DROP TABLE tenants")
        cursor.execute("ALTER TABLE tenants_new RENAME TO tenants")
        
        # Recreate indexes and constraints
        cursor.execute("CREATE INDEX ix_tenants_room_id ON tenants (room_id)")
        cursor.execute("PRAGMA foreign_keys=on")
        
        # Update alembic_version table to mark migrations as applied
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alembic_version (
                version_num VARCHAR(32) NOT NULL, 
                CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
            )
        """)
        
        # Mark all migrations as applied
        migrations = [
            '5cbc390f092c',  # add_payment_and_rent_history_tables
            'add_room_model',  # add_room_model_and_tenant_room_id
            'make_room_id_non_nullable'  # make_room_id_non_nullable
        ]
        
        for migration in migrations:
            cursor.execute(
                "INSERT OR IGNORE INTO alembic_version (version_num) VALUES (?)",
                (migration,)
            )
        
        conn.commit()
        print("✓ Successfully updated database schema")
        
    except Exception as e:
        conn.rollback()
        print(f"Error updating schema: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        conn.close()

if __name__ == "__main__":
    sys.exit(main())
