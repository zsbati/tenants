import sqlite3
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_database():
    # Get the path to the database
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                         'tenants_manager', 'tenants.db')
    
    print(f"Checking database at: {db_path}")
    
    if not os.path.exists(db_path):
        print("ERROR: Database file does not exist!")
        return
    
    try:
        # Connect to the database
        conn = sqlite3.connect(f'file:{db_path}?mode=ro', uri=True)
        cursor = conn.cursor()
        
        # List all tables
        print("\n=== Tables in database ===")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"Found {len(tables)} tables:")
        for table in tables:
            print(f"- {table[0]}")
        
        # Check if tenants table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tenants';")
        if not cursor.fetchone():
            print("\nERROR: 'tenants' table does not exist!")
            return
        
        # Check tenants table structure
        print("\n=== Tenants table structure ===")
        cursor.execute("PRAGMA table_info(tenants);")
        columns = cursor.fetchall()
        print(f"Found {len(columns)} columns in 'tenants' table:")
        for col in columns:
            print(f"- {col[1]} ({col[2]})")
        
        # Check for required columns
        required_columns = ['id', 'name', 'is_active', 'deleted_at', 'created_at', 'updated_at']
        existing_columns = [col[1] for col in columns]
        missing_columns = [col for col in required_columns if col not in existing_columns]
        
        if missing_columns:
            print(f"\nWARNING: Missing required columns: {', '.join(missing_columns)}")
        else:
            print("\nAll required columns are present in the tenants table.")
        
        # Count tenants
        cursor.execute("SELECT COUNT(*) FROM tenants;")
        count = cursor.fetchone()[0]
        print(f"\nFound {count} tenants in the database.")
        
        # Count active/inactive tenants
        try:
            cursor.execute("SELECT is_active, COUNT(*) FROM tenants GROUP BY is_active;")
            print("\nTenants by status:")
            for status, count in cursor.fetchall():
                print(f"- {'Active' if status else 'Inactive'}: {count}")
        except sqlite3.OperationalError as e:
            print(f"\nCould not query tenant status: {str(e)}")
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"\nDatabase error: {str(e)}")
    except Exception as e:
        print(f"\nError: {str(e)}")

if __name__ == "__main__":
    check_database()
