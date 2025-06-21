"""
Direct test data generator script for the Tenants Manager application.
This script can be run directly without module imports.
"""
import os
import sys
import random
from datetime import datetime, timedelta

try:
    from faker import Faker
    from sqlalchemy import create_engine, Column, Integer, String, Date, DateTime, Float, Boolean, ForeignKey, Enum
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import sessionmaker, relationship
    from enum import Enum as PyEnum
except ImportError as e:
    print("ERROR: Required packages are not installed.")
    print(f"Please run: pip install faker==19.3.0 SQLAlchemy==2.0.21 python-dateutil==2.8.2")
    print(f"Error details: {e}")
    sys.exit(1)

# --- Database Models ---
Base = declarative_base()

class PaymentStatus(PyEnum):
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

class PaymentType(PyEnum):
    RENT = "rent"
    DEPOSIT = "deposit"
    FINE = "fine"
    OTHER = "other"

class EmergencyContact(Base):
    __tablename__ = 'emergency_contacts'
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id'))
    name = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)

class Payment(Base):
    __tablename__ = 'payments'
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    amount = Column(Float, nullable=False)
    payment_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    payment_type = Column(Enum(PaymentType), nullable=False, default=PaymentType.RENT)
    status = Column(Enum(PaymentStatus), nullable=False, default=PaymentStatus.COMPLETED)
    reference_month = Column(Date, nullable=False)
    description = Column(String(200), nullable=True)

class RentHistory(Base):
    __tablename__ = 'rent_history'
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    amount = Column(Float, nullable=False)
    valid_from = Column(DateTime, default=datetime.utcnow, nullable=False)
    valid_to = Column(DateTime, nullable=True)
    changed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    changed_by = Column(String(100), nullable=True)

class Tenant(Base):
    __tablename__ = 'tenants'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    room = Column(String(50), nullable=False)
    rent = Column(Float, nullable=False)
    bi = Column(String(20), unique=True, nullable=False)
    email = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    address = Column(String(200), nullable=True)
    birth_date = Column(Date, nullable=False)
    entry_date = Column(Date, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    deleted_at = Column(DateTime, nullable=True)

# --- Test Data Generation ---
class TestDataGenerator:
    def __init__(self, db_path='test_tenants.db'):
        self.engine = create_engine(f'sqlite:///{db_path}')
        self.Session = sessionmaker(bind=self.engine)
        self.fake = Faker('pt_PT')
        self.rooms = [f"{floor}{chr(room + 64)}" for floor in range(1, 6) for room in range(1, 7)]
    
    def init_db(self):
        """Initialize the test database"""
        Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)
    
    def generate_tenant(self):
        """Generate a single tenant with realistic data"""
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
        return EmergencyContact(
            tenant_id=tenant_id,
            name=self.fake.name(),
            phone=f"9{random.randint(10, 99)}{random.randint(100000, 999999)}",
            email=self.fake.email()
        )
    
    def generate_rent_history(self, tenant_id, entry_date, current_rent):
        """Generate rent history for a tenant"""
        histories = []
        current_date = entry_date
        today = datetime.now()
        
        # Initial rent (slightly lower than current rent)
        initial_rent = round(current_rent * random.uniform(0.8, 0.95), 2)
        
        # First rent entry
        first_change_date = current_date + timedelta(days=random.randint(30, 180))
        histories.append(RentHistory(
            tenant_id=tenant_id,
            amount=initial_rent,
            valid_from=current_date,
            valid_to=first_change_date,
            changed_at=current_date
        ))
        
        # Subsequent rent changes (0-3 changes)
        num_changes = random.randint(0, 3)
        for _ in range(num_changes):
            change_date = first_change_date + timedelta(days=random.randint(180, 365))
            if change_date > today:
                break
                
            # Update rent with small increase
            initial_rent = min(initial_rent * 1.03, current_rent)  # Max 3% increase
            initial_rent = round(initial_rent, 2)
            
            histories.append(RentHistory(
                tenant_id=tenant_id,
                amount=initial_rent,
                valid_from=first_change_date,
                valid_to=change_date,
                changed_at=first_change_date
            ))
            
            first_change_date = change_date
        
        # Current rent
        histories.append(RentHistory(
            tenant_id=tenant_id,
            amount=current_rent,
            valid_from=first_change_date,
            valid_to=None,
            changed_at=first_change_date
        ))
        
        return histories
    
    def generate_payments(self, tenant_id, entry_date, monthly_rent):
        """Generate payment history for a tenant"""
        payments = []
        current_date = entry_date
        today = datetime.now()
        
        # Generate payments for each month
        while current_date < today:
            # Skip some months randomly (5% chance of missing a payment)
            if random.random() > 0.05:
                payment_date = current_date + timedelta(days=random.randint(0, 5))  # Payment within 5 days of due date
                
                # Sometimes pay multiple months at once (10% chance)
                if random.random() < 0.1 and current_date + timedelta(days=30) < today:
                    amount = monthly_rent * random.randint(2, 4)
                    payment_date += timedelta(days=random.randint(0, 30))
                else:
                    amount = monthly_rent
                
                payments.append(Payment(
                    tenant_id=tenant_id,
                    amount=amount,
                    payment_date=payment_date,
                    payment_type=PaymentType.RENT,
                    status=PaymentStatus.COMPLETED,
                    reference_month=current_date.date(),
                    description=f"Rent for {current_date.strftime('%B %Y')}"
                ))
            
            # Move to next month
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1, day=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1, day=1)
        
        return payments
    
    def generate_test_data(self, num_tenants=50):
        """Generate test data for the specified number of tenants"""
        print(f"Generating test data for {num_tenants} tenants...")
        
        # Initialize database
        self.init_db()
        
        with self.Session() as session:
            for i in range(1, num_tenants + 1):
                # Generate tenant
                tenant = self.generate_tenant()
                session.add(tenant)
                session.flush()  # Get the tenant ID
                
                # Add emergency contact for active tenants
                if tenant.is_active and random.random() > 0.2:  # 80% chance of having emergency contact
                    contact = self.generate_emergency_contact(tenant.id)
                    session.add(contact)
                
                # Generate rent history
                entry_date = tenant.entry_date if isinstance(tenant.entry_date, datetime) else datetime.combine(tenant.entry_date, datetime.min.time())
                rent_histories = self.generate_rent_history(tenant.id, entry_date, tenant.rent)
                for history in rent_histories:
                    session.add(history)
                
                # Generate payments
                payments = self.generate_payments(tenant.id, entry_date, tenant.rent)
                for payment in payments:
                    session.add(payment)
                
                # Commit every 10 tenants
                if i % 10 == 0:
                    session.commit()
                    print(f"Generated {i} tenants...")
            
            # Final commit
            session.commit()
        
        print(f"\nSuccessfully generated test data for {num_tenants} tenants in 'test_tenants.db'")
        print("You can now run your application with this test database.")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate test data for Tenants Manager')
    parser.add_argument('num_tenants', type=int, nargs='?', default=50,
                       help='Number of test tenants to generate (default: 50)')
    parser.add_argument('--db', default='test_tenants.db',
                       help='Database filename (default: test_tenants.db)')
    
    args = parser.parse_args()
    
    print("=== Tenants Manager Test Data Generator ===")
    print(f"Python version: {sys.version}")
    print(f"Generating {args.num_tenants} test tenants in '{args.db}'...\n")
    
    try:
        generator = TestDataGenerator(args.db)
        generator.generate_test_data(args.num_tenants)
    except Exception as e:
        print(f"\nError generating test data: {e}")
        print("\nMake sure you have all required packages installed:")
        print("pip install faker==19.3.0 SQLAlchemy==2.0.21 python-dateutil==2.8.2")
        sys.exit(1)
