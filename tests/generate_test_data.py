import random
from datetime import datetime, timedelta
from faker import Faker
from sqlalchemy.exc import IntegrityError
from tenants_manager.models.tenant import Tenant, EmergencyContact, Payment, RentHistory, PaymentStatus, PaymentType
from tenants_manager.utils.database import DatabaseManager
from sqlalchemy.orm import sessionmaker
import sys
import os

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

fake = Faker()

def generate_tenant():
    """Generate a random tenant with realistic data"""
    entry_date = fake.date_between(start_date='-5y', end_date='today')
    birth_date = fake.date_of_birth(minimum_age=18, maximum_age=90)
    
    tenant = Tenant(
        name=fake.name(),
        room=f"{random.randint(1, 50)}{random.choice(['A', 'B', 'C', 'D'])}",
        rent=round(random.uniform(300, 1500), 2),
        bi=fake.unique.bothify(text='###########'),
        email=fake.unique.email(),
        phone=fake.phone_number()[:20],
        address=fake.address().replace('\n', ', ')[:200],
        birth_date=birth_date,
        entry_date=entry_date,
        is_active=random.choices([True, False], weights=[0.9, 0.1])[0]
    )
    
    # Add emergency contact for active tenants
    if tenant.is_active:
        tenant.emergency_contact = EmergencyContact(
            name=fake.name(),
            phone=fake.phone_number()[:20],
            email=fake.email()
        )
    
    return tenant

def generate_rent_history(tenant, session):
    """Generate realistic rent history for a tenant"""
    current_date = tenant.entry_date
    end_date = datetime.now().date()
    
    # Initial rent
    current_rent = tenant.rent
    
    # Generate rent changes (0 to 3 changes per tenant)
    for _ in range(random.randint(0, 3)):
        if current_date >= end_date:
            break
            
        # Create a rent change record
        change_date = fake.date_between(
            start_date=current_date + timedelta(days=30),
            end_date=min(current_date + timedelta(days=365*2), end_date)
        )
        
        # Update current rent (between -10% and +20% of current rent)
        current_rent = round(current_rent * random.uniform(0.9, 1.2), 2)
        
        # Create rent history record
        rent_history = RentHistory(
            tenant=tenant,
            amount=current_rent,
            valid_from=change_date,
            changed_by="system"
        )
        
        session.add(rent_history)
        current_date = change_date
    
    return tenant

def generate_payments(tenant, session):
    """Generate payment history for a tenant"""
    current_date = tenant.entry_date
    end_date = datetime.now().date()
    
    # Generate monthly payments
    while current_date < end_date:
        # Skip some payments to simulate late/missed payments (10% chance)
        if random.random() > 0.1:
            payment_date = current_date + timedelta(days=random.randint(-5, 5))
            
            # Get the rent amount for this period
            rent_amount = get_rent_for_date(tenant, current_date)
            
            # Create payment (sometimes partial, sometimes full)
            if random.random() > 0.9:  # 10% chance of partial payment
                amount = round(rent_amount * random.uniform(0.1, 0.9), 2)
            else:
                amount = rent_amount
            
            payment = Payment(
                tenant=tenant,
                amount=amount,
                payment_date=payment_date,
                payment_type=PaymentType.RENT,
                status=PaymentStatus.COMPLETED,
                reference_month=current_date.replace(day=1)
            )
            
            session.add(payment)
        
        # Move to next month
        if current_date.month == 12:
            current_date = current_date.replace(year=current_date.year + 1, month=1, day=1)
        else:
            current_date = current_date.replace(month=current_date.month + 1, day=1)
    
    return tenant

def get_rent_for_date(tenant, date):
    """Get the rent amount for a specific date"""
    # Sort rent history by valid_from date (newest first)
    sorted_history = sorted(tenant.rent_history, key=lambda x: x.valid_from, reverse=True)
    
    # Find the most recent rent history record that's valid for the given date
    for record in sorted_history:
        if record.valid_from <= date and (record.valid_to is None or record.valid_to >= date):
            return record.amount
    
    # If no history record found, use the current rent
    return tenant.rent

def generate_test_data(num_tenants=100):
    """Generate test data for the application"""
    db = DatabaseManager()
    Session = db.get_session()
    session = Session()
    
    try:
        print(f"Generating {num_tenants} test tenants...")
        
        for i in range(num_tenants):
            # Generate tenant
            tenant = generate_tenant()
            session.add(tenant)
            
            # Generate rent history
            generate_rent_history(tenant, session)
            
            # Generate payments
            generate_payments(tenant, session)
            
            if (i + 1) % 10 == 0:
                print(f"Generated {i + 1} tenants...")
                session.commit()
        
        session.commit()
        print(f"Successfully generated {num_tenants} test tenants with rent history and payments.")
        
    except Exception as e:
        session.rollback()
        print(f"Error generating test data: {str(e)}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    # Generate 100 test tenants by default, or specify a different number
    num_tenants = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    generate_test_data(num_tenants)
