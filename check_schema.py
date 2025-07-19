import sqlite3
import os

def check_schema():
    db_path = os.path.join('tenants_manager', 'tenants.db')
    if not os.path.exists(db_path):
        print(f"Database file not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check tenants table
    print("\n=== Tenants Table ===")
    cursor.execute('PRAGMA table_info(tenants)')
    print("Columns:")
    for col in cursor.fetchall():
        print(f"- {col[1]} ({col[2]}){' NOT NULL' if col[3] else ''}")
    
    # Check rooms table
    print("\n=== Rooms Table ===")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='rooms'")
    if cursor.fetchone():
        cursor.execute('PRAGMA table_info(rooms)')
        print("Columns:")
        for col in cursor.fetchall():
            print(f"- {col[1]} ({col[2]}){' NOT NULL' if col[3] else ''}")
    else:
        print("Rooms table does not exist")
    
    # Check foreign key constraints
    print("\n=== Foreign Keys ===")
    cursor.execute("PRAGMA foreign_key_list('tenants')")
    fks = cursor.fetchall()
    if fks:
        print("Foreign Keys:")
        for fk in fks:
            print(f"- {fk[3]} -> {fk[2]}.{fk[4]}")
    else:
        print("No foreign key constraints found on tenants table")
    
    conn.close()

if __name__ == "__main__":
    check_schema()
