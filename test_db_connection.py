import sys
import os
import traceback
from datetime import datetime

# Enable SQLAlchemy logging
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import after setting up logging
os.environ['SQLALCHEMY_WARN_20'] = '1'
os.environ['SQLALCHEMY_SILENCE_UBER_WARNING'] = '1'

print("Python version:", sys.version)
print("Current working directory:", os.getcwd())

# Now import SQLAlchemy related modules
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

# Import application modules
try:
    from tenants_manager.utils.database import DatabaseManager
    from tenants_manager.models.tenant import Base, Tenant, Payment, RentHistory, EmergencyContact
    print("Successfully imported application modules")
except ImportError as e:
    print(f"Error importing modules: {e}")
    traceback.print_exc()
    sys.exit(1)

def test_connection():
    print("\n=== Starting database connection test ===")
    
    try:
        # Print environment information
        print("\nEnvironment:")
        print(f"- Python executable: {sys.executable}")
        print(f"- Current directory: {os.getcwd()}")
        
        # Initialize database manager
        print("\nInitializing DatabaseManager...")
        db = DatabaseManager()
        
        # Print database path
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tenants_manager', 'tenants.db')
        print(f"Database path: {db_path}")
        print(f"Database exists: {os.path.exists(db_path)}")
        if os.path.exists(db_path):
            print(f"Database size: {os.path.getsize(db_path)} bytes")
        
        # Create a test engine with echo=True for SQL output
        test_engine = create_engine(f'sqlite:///{db_path}', echo=True)
        print("\nTesting direct SQLAlchemy connection...")
        
        # Test raw connection
        with test_engine.connect() as conn:
            print("Successfully connected to database")
            result = conn.execute("SELECT sqlite_version()")
            print(f"SQLite version: {result.scalar()}")
        
        # Test ORM mapping
        print("\nTesting ORM mapping...")
        Session = sessionmaker(bind=test_engine)
        session = Session()
        
        try:
            # Check if tables exist
            inspector = inspect(test_engine)
            tables = inspector.get_table_names()
            print("\nTables in database:", tables)
            
            # Check each table
            for table_name in tables:
                print(f"\nTable: {table_name}")
                try:
                    # Print table info
                    columns = inspector.get_columns(table_name)
                    print(f"  Columns: {[col['name'] for col in columns]}")
                    
                    # Count rows
                    count = session.execute(f"SELECT COUNT(*) FROM {table_name}").scalar()
                    print(f"  Rows: {count}")
                    
                    # Print sample data (first 2 rows)
                    if count > 0:
                        print("  Sample data:")
                        rows = session.execute(f"SELECT * FROM {table_name} LIMIT 2").fetchall()
                        for i, row in enumerate(rows, 1):
                            print(f"    Row {i}: {dict(row._mapping)}")
                    
                except Exception as e:
                    print(f"  Error inspecting table: {e}")
            
            # Test model queries
            print("\nTesting Tenant model queries...")
            tenant_count = session.query(Tenant).count()
            print(f"Found {tenant_count} tenants in the database")
            
            if tenant_count > 0:
                first_tenant = session.query(Tenant).first()
                print(f"First tenant: {first_tenant.name} (ID: {first_tenant.id})")
            
            return True
            
        except Exception as e:
            print(f"\n!!! ERROR during ORM operations: {e}")
            traceback.print_exc()
            return False
        finally:
            session.close()
            
    except Exception as e:
        print(f"\n!!! CRITICAL ERROR: {e}")
        traceback.print_exc()
        return False
    finally:
        print("\n=== Test completed ===")

if __name__ == "__main__":
    if test_connection():
        print("\nDatabase connection test completed successfully!")
    else:
        print("\nDatabase connection test failed!")
