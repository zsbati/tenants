import unittest
import os
import sys
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tenants_manager.models.tenant import Tenant, Base, EmergencyContact, Payment, RentHistory
from tenants_manager.utils.database import DatabaseManager

class TestSoftDelete(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test database and session"""
        cls.db_manager = DatabaseManager()
        # Use an in-memory SQLite database for testing
        cls.db_manager.engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(cls.db_manager.engine)
        cls.Session = sessionmaker(bind=cls.db_manager.engine)
        cls.db_manager.Session = cls.Session
        
    def setUp(self):
        """Create a new session for each test"""
        self.session = self.Session()
        self.addCleanup(self.session.close)
        
        # Create a test tenant
        self.tenant = Tenant(
            name="Test Tenant",
            room="101",
            rent=1000.0,
            bi="123456789",
            email="test@example.com",
            phone="1234567890",
            birth_date=datetime.now().date() - timedelta(days=365*25),
            entry_date=datetime.now().date() - timedelta(days=100)
        )
        self.session.add(self.tenant)
        self.session.commit()
    
    def test_soft_delete_tenant(self):
        """Test soft deleting a tenant"""
        # Verify tenant is active initially
        self.assertTrue(self.tenant.is_active)
        self.assertIsNone(self.tenant.deleted_at)
        
        # Soft delete the tenant
        self.tenant.soft_delete()
        self.session.commit()
        
        # Verify soft delete fields are updated
        self.assertFalse(self.tenant.is_active)
        self.assertIsNotNone(self.tenant.deleted_at)
        
        # Verify tenant is not in default queries
        tenant_from_db = self.db_manager.get_tenant_by_id(self.tenant.id)
        self.assertIsNone(tenant_from_db)
        
        # Verify tenant is in queries when including inactive
        tenant_from_db = self.db_manager.get_tenant_by_id(self.tenant.id, include_inactive=True)
        self.assertIsNotNone(tenant_from_db)
        self.assertEqual(tenant_from_db.id, self.tenant.id)
    
    def test_restore_tenant(self):
        """Test restoring a soft-deleted tenant"""
        # Soft delete the tenant first
        self.tenant.soft_delete()
        self.session.commit()
        
        # Restore the tenant
        self.tenant.restore()
        self.session.commit()
        
        # Verify tenant is active and can be retrieved
        self.assertTrue(self.tenant.is_active)
        self.assertIsNone(self.tenant.deleted_at)
        
        tenant_from_db = self.db_manager.get_tenant_by_id(self.tenant.id)
        self.assertIsNotNone(tenant_from_db)
        self.assertEqual(tenant_from_db.id, self.tenant.id)
    
    def test_get_tenants_excludes_deleted(self):
        """Test that get_tenants excludes soft-deleted tenants by default"""
        # Create a second tenant
        tenant2 = Tenant(
            name="Another Tenant",
            room="102",
            rent=1100.0,
            bi="987654321",
            email="another@example.com",
            phone="0987654321",
            birth_date=datetime.now().date() - timedelta(days=365*30),
            entry_date=datetime.now().date() - timedelta(days=50)
        )
        self.session.add(tenant2)
        self.session.commit()
        
        # Get all tenants (should be 2)
        tenants, total = self.db_manager.get_tenants()
        self.assertEqual(total, 2)
        self.assertEqual(len(tenants), 2)
        
        # Soft delete one tenant
        self.tenant.soft_delete()
        self.session.commit()
        
        # Get all tenants (should be 1)
        tenants, total = self.db_manager.get_tenants()
        self.assertEqual(total, 1)
        self.assertEqual(len(tenants), 1)
        self.assertEqual(tenants[0].id, tenant2.id)
        
        # Get all tenants including deleted (should be 2)
        tenants, total = self.db_manager.get_tenants(include_inactive=True)
        self.assertEqual(total, 2)
        self.assertEqual(len(tenants), 2)

if __name__ == '__main__':
    unittest.main()
