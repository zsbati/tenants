import sqlite3
import os

def check_database(db_path):
    print(f"\nChecking database at: {db_path}")
    
    if not os.path.exists(db_path):
        print("  - Database file does not exist!")
        return False
    
    try:
        # Connect to the database
        conn = sqlite3.connect(f'file:{db_path}?mode=ro', uri=True)
        cursor = conn.cursor()
        
        # List all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [t[0] for t in cursor.fetchall()]
        print(f"  - Found {len(tables)} tables: {', '.join(tables) if tables else 'None'}")
        
        # Check if tenants table exists
        if 'tenants' in tables:
            print("  - 'tenants' table found!")
            cursor.execute("PRAGMA table_info(tenants);")
            columns = [c[1] for c in cursor.fetchall()]
            print(f"  - Tenants table columns: {', '.join(columns)}")
            
            # Check for required columns
            required_columns = ['id', 'name', 'is_active', 'deleted_at', 'created_at', 'updated_at']
            missing_columns = [col for col in required_columns if col not in columns]
            
            if missing_columns:
                print(f"  - WARNING: Missing required columns: {', '.join(missing_columns)}")
            
            # Count tenants
            cursor.execute("SELECT COUNT(*) FROM tenants;")
            count = cursor.fetchone()[0]
            print(f"  - Total tenants: {count}")
            
            # Count active/inactive tenants if is_active column exists
            if 'is_active' in columns:
                cursor.execute("SELECT is_active, COUNT(*) FROM tenants GROUP BY is_active;")
                print("  - Tenants by status:")
                for status, count in cursor.fetchall():
                    print(f"    - {'Active' if status else 'Inactive'}: {count}")
        
        conn.close()
        return True
        
    except sqlite3.Error as e:
        print(f"  - Database error: {str(e)}")
        return False
    except Exception as e:
        print(f"  - Error: {str(e)}")
        return False

if __name__ == "__main__":
    # List of possible database locations
    db_paths = [
        'tenants_manager/tenants.db',
        'data/tenants.db',
        'tenants.db',
        '../tenants_manager/tenants.db',
        '../../tenants_manager/tenants.db',
    ]
    
    print("=== Checking all possible database locations ===")
    found = False
    for db_path in db_paths:
        if check_database(db_path):
            found = True
    
    if not found:
        print("\nNo valid database files were found in any of the expected locations.")
        print("Please ensure the database exists in one of these locations:")
        for path in db_paths:
            print(f"- {os.path.abspath(path)}")
    else:
        print("\nDatabase check completed successfully.")
