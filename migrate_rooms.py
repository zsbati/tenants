import sys
import logging
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from tenants_manager.utils.database import DatabaseManager
from tenants_manager.models.tenant import Room, Tenant

def migrate_rooms():
    """Migrate room data from string to Room model."""
    db = DatabaseManager()
    session = db.Session()
    
    try:
        # Get all unique room strings from tenants
        room_strings = session.query(Tenant.room).distinct().all()
        room_strings = [r[0] for r in room_strings if r[0]]  # Extract strings and filter out None
        
        print(f"Found {len(room_strings)} unique room strings in tenants.")
        
        # Create Room entries for each unique room string
        room_map = {}
        for room_name in room_strings:
            # Check if room already exists (in case of multiple runs)
            existing_room = session.query(Room).filter_by(name=room_name).first()
            if existing_room:
                room_map[room_name] = existing_room
                print(f"Room '{room_name}' already exists with ID {existing_room.id}")
                continue
                
            # Create new room with default capacity of 4
            new_room = Room(
                name=room_name,
                capacity=4,  # Default capacity
                description=f"Migrated room for {room_name}"
            )
            session.add(new_room)
            session.flush()  # Get the new room's ID
            room_map[room_name] = new_room
            print(f"Created room '{room_name}' with ID {new_room.id}")
        
        # Update all tenants with their corresponding room_id
        tenants = session.query(Tenant).all()
        updated_count = 0
        
        for tenant in tenants:
            if not tenant.room:
                print(f"Warning: Tenant {tenant.id} has no room assigned")
                continue
                
            room = room_map.get(tenant.room)
            if room and tenant.room_id != room.id:
                tenant.room_id = room.id
                updated_count += 1
        
        # Commit all changes
        session.commit()
        print(f"Migration complete. Updated {updated_count} tenants with room assignments.")
        
        # Verify the migration
        tenants_without_room = session.query(Tenant).filter(Tenant.room_id.is_(None)).count()
        print(f"Tenants without room assignment after migration: {tenants_without_room}")
        
        # Print room occupancy
        print("\nRoom occupancy after migration:")
        rooms = session.query(Room).all()
        for room in rooms:
            print(f"Room {room.name} (ID: {room.id}): {room.current_occupancy} tenants")
        
    except Exception as e:
        session.rollback()
        print(f"Error during migration: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    print("Starting room migration...")
    migrate_rooms()
    print("\nMigration completed. Please review the output above for any issues.")
