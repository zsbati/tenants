import sys
import os

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils.database import DatabaseManager

def main():
    manager = DatabaseManager()
    manager.initialize_database()
    print("Database initialized successfully!")

if __name__ == "__main__":
    main()
