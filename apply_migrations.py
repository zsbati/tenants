"""
Script to manually apply database migrations in the correct order.
Run this script to update the database schema.
"""
import os
import sys
import sqlite3
import importlib.util
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

# Import the database URL function directly to avoid circular imports
from tenants_manager.config.database import get_database_url

def run_sql_script(conn, script_path):
    """Run a SQL script from a file."""
    with open(script_path, 'r', encoding='utf-8') as f:
        sql_script = f.read()
    
    # Split the script into individual statements
    statements = [stmt.strip() for stmt in sql_script.split(';') if stmt.strip()]
    
    cursor = conn.cursor()
    for stmt in statements:
        try:
            cursor.execute(stmt)
        except sqlite3.OperationalError as e:
            print(f"Warning: {e}")
    conn.commit()

def load_migration_module(migration_name):
    """Dynamically load a migration module."""
    migrations_dir = project_root / 'migrations' / 'versions'
    module_name = None
    
    # Find the migration file
    for file in migrations_dir.glob('*.py'):
        if file.stem.startswith(migration_name) or migration_name in file.stem:
            module_name = file.stem
            break
    
    if not module_name:
        raise ImportError(f"Could not find migration: {migration_name}")
    
    # Dynamically import the module
    spec = importlib.util.spec_from_file_location(
        f"migrations.versions.{module_name}",
        migrations_dir / f"{module_name}.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module

def main():
    # Get the database URL
    db_url = get_database_url()
    db_path = db_url.replace('sqlite:///', '')
    
    # Check if database exists
    if not os.path.exists(db_path):
        print(f"Error: Database file not found at {db_path}")
        return 1
    
    print(f"Applying migrations to database: {db_path}")
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    
    try:
        # Create alembic_version table if it doesn't exist
        conn.execute("""
            CREATE TABLE IF NOT EXISTS alembic_version (
                version_num VARCHAR(32) NOT NULL, 
                CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
            )
        """)
        
        # Check which migrations have been applied
        cursor = conn.cursor()
        cursor.execute("SELECT version_num FROM alembic_version")
        applied_migrations = {row[0] for row in cursor.fetchall()}
        
        # Define migrations in the correct order
        migrations = [
            '5cbc390f092c',  # add_payment_and_rent_history_tables
            'add_room_model_and_tenant_room_id',  # Add room model and room_id column
            'make_room_id_non_nullable'  # Make room_id non-nullable and remove room column
        ]
        
        # Apply migrations
        for migration in migrations:
            if migration not in applied_migrations:
                print(f"\n--- Applying migration: {migration} ---")
                
                try:
                    # Load and run the migration
                    migration_module = load_migration_module(migration)
                    migration_module.upgrade()
                    
                    # Record the migration
                    cursor.execute("INSERT INTO alembic_version (version_num) VALUES (?)", (migration,))
                    conn.commit()
                    print(f"✓ Successfully applied migration: {migration}")
                    
                except Exception as e:
                    conn.rollback()
                    print(f"✗ Error applying migration {migration}: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    return 1
            else:
                print(f"- Migration already applied: {migration}")
        
        print("\nAll migrations applied successfully!")
        return 0
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        conn.close()

if __name__ == "__main__":
    sys.exit(main())
