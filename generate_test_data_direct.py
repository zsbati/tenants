"""
Direct test data generator script for the Tenants Manager application.
This script generates test data using the application's models.
"""
import os
import sys
import random
import logging
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)
logger.info(f"Added project root to Python path: {project_root}")

try:
    logger.info("Importing required packages...")
    from faker import Faker
    from sqlalchemy import create_engine, inspect
    from sqlalchemy.orm import sessionmaker
    from tenants_manager.models.tenant import (
        Base, Tenant, EmergencyContact, Payment, RentHistory,
        PaymentStatus, PaymentType
    )
    logger.info("Successfully imported all required packages")
except ImportError as e:
    logger.error("ERROR: Required packages are not installed or there was an import error.")
    logger.error(f"Please run: pip install -r requirements.txt")
    logger.error(f"Error details: {e}")
    sys.exit(1)

# --- Test Data Generation ---
class TestDataGenerator:
    def __init__(self, db_path='tenants_manager/tenants.db'):
        # Ensure the directory exists
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        self.engine = create_engine(f'sqlite:///{db_path}')
        self.Session = sessionmaker(bind=self.engine)
        self.fake = Faker('pt_PT')
        self.rooms = [f"{floor}{chr(room + 64)}" for floor in range(1, 6) for room in range(1, 7)]
        self.db_path = db_path
        
        # Set up the database schema
        self.init_db()
    
    def init_db(self):
        """Initialize the test database"""
        logger.info(f"Initializing database at {self.db_path}")
        try:
            logger.info("Dropping all existing tables...")
            Base.metadata.drop_all(self.engine)
            logger.info("Creating all tables...")
            Base.metadata.create_all(self.engine)
            
            # Verify tables were created
            inspector = inspect(self.engine)
            tables = inspector.get_table_names()
            logger.info(f"Database initialized. Tables created: {tables}")
            return True
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            return False
    
    def generate_tenant(self):
        """Generate a single tenant with realistic data"""
        logger.debug("Generating tenant data...")
        entry_date = self.fake.date_between(start_date='-5y', end_date='today')
        birth_date = self.fake.date_of_birth(minimum_age=18, maximum_age=90)
        
        return Tenant(
            name=self.fake.name(),
            room=random.choice(self.rooms),
            rent=round(random.uniform(300, 800), 2),
            bi=str(random.randint(10000000, 99999999)),
            email=self.fake.email(),
            phone=f"9{random.randint(10, 99)}{random.randint(100000, 999999)}",
            address=self.fake.address().replace('\n', ', ')[:200],
            birth_date=birth_date,
            entry_date=entry_date,
            is_active=random.choices([True, False], weights=[0.9, 0.1])[0]
        )
    
    def generate_emergency_contact(self, tenant_id):
        """Generate an emergency contact for a tenant"""
        logger.debug(f"Generating emergency contact for tenant {tenant_id}")
        try:
            contact = EmergencyContact(
                tenant_id=tenant_id,
                name=self.fake.name(),
                phone=self.fake.phone_number(),
                email=self.fake.email()
            )
            logger.debug(f"Generated contact: {contact.name} ({contact.email})")
            return contact
        except Exception as e:
            logger.error(f"Error generating emergency contact: {e}")
            raise
    
    def generate_rent_history(self, tenant_id, rent_amount, entry_date):
        """Generate rent history for a tenant"""
        logger.debug(f"Generating rent history for tenant {tenant_id}")
        try:
            history = RentHistory(
                tenant_id=tenant_id,
                amount=rent_amount,
                valid_from=entry_date,
                valid_to=None,
                changed_at=datetime.utcnow(),
                changed_by='system'
            )
            logger.debug(f"Generated rent history: {history.amount} from {history.valid_from}")
            return history
        except Exception as e:
            logger.error(f"Error generating rent history: {e}")
            raise
    
    def generate_payment(self, tenant_id, reference_month):
        """Generate a payment for a tenant"""
        logger.debug(f"Generating payment for tenant {tenant_id} for {reference_month}")
        try:
            payment = Payment(
                tenant_id=tenant_id,
                amount=round(random.uniform(200, 1000), 2),
                payment_date=self.fake.date_between(start_date=reference_month, end_date='today'),
                payment_type=random.choice(list(PaymentType)),
                status=random.choice(list(PaymentStatus)),
                reference_month=reference_month,
                description=f"Payment for {reference_month.strftime('%B %Y')}"
            )
            logger.debug(f"Generated payment of {payment.amount} {payment.payment_type}")
            return payment
        except Exception as e:
            logger.error(f"Error generating payment: {e}")
            raise
    
    def generate_tenants(self, count=10):
        """Generate test tenants with related data"""
        logger.info(f"Starting to generate {count} tenants...")
        session = self.Session()
        success_count = 0
        
        try:
            for i in range(count):
                try:
                    logger.info(f"Generating tenant {i+1}/{count}...")
                    tenant = self.generate_tenant()
                    session.add(tenant)
                    session.flush()  # To get the tenant ID
                    logger.debug(f"Created tenant: {tenant.name} (ID: {tenant.id})")
                    
                    # Add emergency contact
                    contact = self.generate_emergency_contact(tenant.id)
                    session.add(contact)
                    logger.debug(f"Added emergency contact: {contact.name}")
                    
                    # Add rent history
                    rent_history = self.generate_rent_history(tenant.id, tenant.rent, tenant.entry_date)
                    session.add(rent_history)
                    logger.debug(f"Added rent history: {rent_history.amount} from {rent_history.valid_from}")
                    
                    # Add some payments
                    months_since_entry = (datetime.now().date() - tenant.entry_date).days // 30
                    payment_count = min(12, max(1, months_since_entry))  # 1-12 months of payments
                    logger.debug(f"Generating {payment_count} payments...")
                    
                    for month in range(1, payment_count + 1):
                        reference_month = tenant.entry_date + timedelta(days=30 * (month - 1))
                        payment = self.generate_payment(tenant.id, reference_month)
                        session.add(payment)
                    
                    # Commit after each tenant to avoid large transactions
                    session.commit()
                    success_count += 1
                    logger.info(f"Successfully generated tenant {i+1}/{count}")
                    
                except Exception as e:
                    logger.error(f"Error generating tenant {i+1}: {e}")
                    session.rollback()
                    # Continue with next tenant even if one fails
                    continue
            
            logger.info(f"Successfully generated {success_count} out of {count} tenants")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Fatal error in generate_tenants: {e}")
            session.rollback()
            return False
        finally:
            session.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate test data for Tenants Manager')
    parser.add_argument('count', type=int, nargs='?', default=10, 
                      help='Number of tenants to generate (default: 10)')
    parser.add_argument('--db', type=str, default='tenants_manager/tenants.db', 
                      help='Path to the SQLite database file')
    parser.add_argument('--debug', action='store_true',
                      help='Enable debug logging')
    
    args = parser.parse_args()
    
    # Set log level based on debug flag
    if args.debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    
    logger.info(f"Tenant Manager Test Data Generator")
    logger.info(f"Generating {args.count} test tenants in database: {args.db}")
    
    try:
        # Initialize the generator
        generator = TestDataGenerator(db_path=args.db)
        
        # Generate test data
        success = generator.generate_tenants(args.count)
        
        if success:
            logger.info("Test data generation completed successfully!")
            sys.exit(0)
        else:
            logger.error("Test data generation failed. Check the logs above for errors.")
            sys.exit(1)
            
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
