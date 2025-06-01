from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from ..models.tenant import Base
import os

# Add project root to Python path
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

class DatabaseManager:
    def __init__(self):
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tenants.db')
        self.engine = create_engine(f'sqlite:///{db_path}')
        self.Session = sessionmaker(bind=self.engine)
    
    def initialize_database(self):
        Base.metadata.create_all(self.engine)

    def add_tenant(self, tenant):
        """Add a new tenant to the database"""
        with self.Session() as session:
            try:
                session.add(tenant)
                session.commit()
                return True
            except Exception as e:
                session.rollback()
                print(f"Error adding tenant: {str(e)}")
                return False

    def get_tenants(self):
        """Get all tenants from the database"""
        with self.Session() as session:
            try:
                return session.query(Tenant).all()
            except Exception as e:
                print(f"Error getting tenants: {str(e)}")
                return []
    
    def get_session(self):
        return self.Session()
