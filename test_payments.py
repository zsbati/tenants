from datetime import datetime, date, timedelta
from tenants_manager.models.tenant import Tenant, PaymentStatus, PaymentType, RentHistory
from tenants_manager.utils.database import DatabaseManager

def setup_test_data():
    db = DatabaseManager()
    
    # Create a test tenant if not exists
    with db.get_session() as session:
        # Check if test tenant exists
        tenant = session.query(Tenant).filter_by(name="Test Tenant").first()
        
        if not tenant:
            # Create a new test tenant
            tenant = Tenant(
                name="Test Tenant",
                room="T-101",
                rent=800.0,
                bi="123456789",
                email="test@example.com",
                phone="1234567890",
                address="123 Test St",
                birth_date=date(1990, 1, 1),
                entry_date=date(2023, 1, 1)
            )
            session.add(tenant)
            session.commit()
            print("Created new test tenant")
        
        return tenant.id

def test_rent_update():
    db = DatabaseManager()
    tenant_id = setup_test_data()
    
    with db.get_session() as session:
        tenant = session.query(Tenant).get(tenant_id)
        print(f"\nCurrent rent: {tenant.rent}")
        
        # Update rent and track history
        print("\nUpdating rent to 850.0...")
        tenant.update_rent(850.0, changed_by="Admin")
        
        # Get rent history
        history = db.get_rent_history(tenant_id)
        print("\nRent History:")
        for record in history:
            print(f"{record.valid_from.date()}: {record.amount} (changed by {record.changed_by or 'system'})")

def test_payment_recording():
    db = DatabaseManager()
    tenant_id = setup_test_data()
    
    # Record a payment
    payment = db.record_payment(
        tenant_id=tenant_id,
        amount=850.0,
        payment_date=datetime.now(),
        payment_type=PaymentType.RENT,
        reference_month=date.today().replace(day=1),
        description="June 2023 Rent"
    )
    
    if payment:
        print("\nRecorded payment:")
        print(f"ID: {payment.id}")
        print(f"Amount: {payment.amount}")
        print(f"Date: {payment.payment_date}")
        print(f"Type: {payment.payment_type}")
        print(f"Description: {payment.description}")
    
    # Get current balance
    balance = db.get_tenant_balance(tenant_id)
    print(f"\nCurrent balance: {balance:.2f}")

def test_statement_generation():
    db = DatabaseManager()
    tenant_id = setup_test_data()
    
    # Generate a statement for the last 6 months
    end_date = datetime.now()
    start_date = (end_date - timedelta(days=180)).replace(day=1)
    
    statement = db.generate_rent_statement(tenant_id, start_date, end_date)
    
    if statement:
        print("\n=== RENT STATEMENT ===")
        print(f"Tenant: {statement['tenant'].name}")
        print(f"Period: {start_date.date()} to {end_date.date()}")
        print(f"Opening Balance: {statement['opening_balance']:.2f}")
        print("\nTransactions:")
        
        # Combine and sort all transactions by date
        transactions = statement['rent_charges'] + statement['payments']
        transactions.sort(key=lambda x: x['date'])
        
        for tx in transactions:
            amount = tx['amount']
            amount_str = f"+{amount:.2f}" if amount > 0 else f"{amount:.2f}"
            print(f"{tx['date'].strftime('%Y-%m-%d')} | {tx['type'].upper():<10} | {amount_str:>10} | Balance: {tx['balance']:.2f}")
        
        print("\nSummary:")
        print(f"Total Rent Due: {statement['total_rent_due']:.2f}")
        print(f"Total Payments: {statement['total_payments']:.2f}")
        print(f"Closing Balance: {statement['closing_balance']:.2f}")

if __name__ == "__main__":
    print("=== Testing Rent Update ===")
    test_rent_update()
    
    print("\n=== Testing Payment Recording ===")
    test_payment_recording()
    
    print("\n=== Testing Statement Generation ===")
    test_statement_generation()
