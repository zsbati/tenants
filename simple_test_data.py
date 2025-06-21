import sqlite3
import random
import os
import sys
from datetime import datetime, timedelta
from enum import Enum

# Payment statuses for better readability
class PaymentStatus(Enum):
    PENDING = 'pending'
    COMPLETED = 'completed'
    OVERDUE = 'overdue'
    PARTIAL = 'partial'
    CANCELLED = 'cancelled'

# Payment types
class PaymentType(Enum):
    RENT = 'rent'
    DEPOSIT = 'deposit'
    FINE = 'fine'
    OTHER = 'other'

def create_tables(cursor):
    """Create database tables with all necessary fields"""
    # Tenants table - Updated to match the SQLAlchemy model
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tenants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        room TEXT NOT NULL,
        rent REAL NOT NULL,
        bi TEXT UNIQUE NOT NULL,
        email TEXT,
        phone TEXT,
        address TEXT,
        birth_date DATE NOT NULL,
        entry_date DATE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_active BOOLEAN DEFAULT 1,
        deleted_at TIMESTAMP NULL
    )
    ''')
    
    # Payments table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tenant_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        payment_date TIMESTAMP NOT NULL,
        payment_type TEXT NOT NULL,
        status TEXT NOT NULL,
        reference_month DATE NOT NULL,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
    )
    ''')
    
    # Rent history table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS rent_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tenant_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        valid_from DATE NOT NULL,
        valid_to DATE,
        changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        changed_by TEXT,
        FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
    )
    ''')
    
    # Emergency contacts table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS emergency_contacts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tenant_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        phone TEXT,
        email TEXT,
        relationship TEXT,
        FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
    )
    ''')

def generate_tenant_data():
    """Generate realistic tenant data"""
    # Portuguese names with some special characters
    first_names = [
        'João', 'Maria', 'Pedro', 'Ana', 'Carlos', 'Sofia', 'Miguel', 'Inês', 'Tiago', 'Beatriz',
        'José', 'Teresa', 'António', 'Francisca', 'Manuel', 'Isabel', 'Francisco', 'Ana', 'João',
        'Maria', 'Luís', 'Matilde', 'Duarte', 'Mariana', 'Afonso', 'Carolina', 'Martim', 'Leonor'
    ]
    
    last_names = [
        'Silva', 'Santos', 'Ferreira', 'Pereira', 'Oliveira', 'Costa', 'Rodrigues', 'Martins',
        'Jesus', 'Sousa', 'Lopes', 'Marques', 'Gomes', 'Ribeiro', 'Carvalho', 'Almeida', 'Pinto',
        'Alves', 'Dias', 'Teixeira', 'Monteiro', 'Gonçalves', 'Coelho', 'Rocha', 'Neves', 'Correia'
    ]
    
    # Some special cases
    first_name = random.choice(first_names)
    last_name = random.choice(last_names)
    
    # 5% chance of special characters in name
    if random.random() < 0.05:
        first_name = f"{first_name} d'Ávila"
    
    # 5% chance of compound last name
    if random.random() < 0.05:
        last_name = f"{last_name} {random.choice(last_names)}"
    
    name = f"{first_name} {last_name}"
    
    # Room number (e.g., 1A, 2B, etc.)
    floor = random.randint(1, 5)
    room_letter = chr(65 + random.randint(0, 3))  # A-D
    room = f"{floor}{room_letter}"
    
    # Rent amount (with some variation)
    base_rent = random.choice([300, 350, 400, 450, 500, 550, 600, 650, 700, 750, 800])
    rent = round(base_rent * random.uniform(0.9, 1.1), 2)  # ±10% variation
    
    # BI/ID number
    bi = str(random.randint(10000000, 99999999))
    
    # Contact info
    email = f"{first_name.lower().replace(' ', '')}.{last_name.lower().replace(' ', '')}@example.com"
    phone = f"9{random.randint(10, 99)}{random.randint(100000, 999999)}"
    
    # Address with some variation
    street_types = ['Rua', 'Avenida', 'Travessa', 'Largo', 'Praça']
    street_names = [
        'das Flores', 'do Sol', 'da Liberdade', '25 de Abril', 'da República',
        'dos Bombeiros Voluntários', 'Dr. António José de Almeida', 'Dom João IV',
        'Almirante Reis', 'Almirante Gago Coutinho', 'Infante D. Henrique'
    ]
    
    address_type = random.choice(street_types)
    street_name = random.choice(street_names)
    number = random.randint(1, 300)
    floor_info = f", {random.randint(1, 10)}º {random.choice(['D', 'E', 'F', ''])}"
    postal_code = f"{random.randint(1000, 4999)}-{random.randint(100, 999)} {random.choice(['Lisboa', 'Porto', 'Braga', 'Coimbra', 'Faro'])}"
    
    address = f"{address_type} {street_name}, {number}{floor_info if random.random() > 0.7 else ''}, {postal_code}"
    
    # Dates
    today = datetime.now()
    max_age = 80
    min_age = 18
    birth_date = today - timedelta(days=random.randint(min_age*365, max_age*365))
    
    # Entry date (1 month to 5 years ago)
    entry_date = today - timedelta(days=random.randint(30, 5*365))
    
    # Active status (80% active)
    is_active = random.random() < 0.8
    
    # 10% chance of having notes
    notes = None
    if random.random() < 0.1:
        notes = random.choice([
            "Prefers email communication",
            "Has a pet (cat)",
            "Special parking space required",
            "Contact only during business hours",
            "Upstairs neighbor complains about noise"
        ])
    
    return {
        'name': name,
        'room': room,
        'rent': rent,
        'bi': bi,
        'email': email,
        'phone': phone,
        'address': address,
        'birth_date': birth_date.date(),
        'entry_date': entry_date.date(),
        'is_active': is_active,
        'notes': notes
    }

def generate_emergency_contact(tenant_id):
    """Generate an emergency contact for a tenant"""
    relationships = ['Mother', 'Father', 'Sister', 'Brother', 'Friend', 'Spouse', 'Child', 'Other Relative']
    
    first_names = ['Ana', 'Maria', 'João', 'Carlos', 'Sofia', 'Miguel', 'Teresa', 'António']
    last_names = ['Silva', 'Santos', 'Oliveira', 'Costa', 'Rodrigues', 'Martins']
    
    name = f"{random.choice(first_names)} {random.choice(last_names)}"
    phone = f"9{random.randint(10, 99)}{random.randint(100000, 999999)}"
    email = f"{name.lower().replace(' ', '.')}@example.com"
    
    return {
        'tenant_id': tenant_id,
        'name': name,
        'phone': phone,
        'email': email,
        'relationship': random.choice(relationships)
    }

def generate_rent_history(tenant_id, entry_date, current_rent):
    """Generate rent history for a tenant"""
    histories = []
    today = datetime.now()
    
    # Start with entry date
    current_date = entry_date
    current_rent_amount = round(current_rent * random.uniform(0.7, 0.9), 2)  # Start with lower rent
    
    # Generate rent changes (0-3 changes)
    num_changes = random.randint(0, 3)
    for _ in range(num_changes + 1):  # +1 to ensure at least one history entry
        if current_date >= today:
            break
            
        # Next change in 6-24 months
        next_change = current_date + timedelta(days=random.randint(180, 720))
        
        # Add history entry
        histories.append({
            'tenant_id': tenant_id,
            'amount': current_rent_amount,
            'valid_from': current_date.date(),
            'valid_to': next_change.date() if next_change < today else None,
            'changed_at': current_date,
            'changed_by': 'system'
        })
        
        # Increase rent for next period (0-5% increase)
        current_rent_amount = round(min(current_rent_amount * random.uniform(1.0, 1.05), current_rent), 2)
        current_date = next_change
    
    return histories

def generate_payments(tenant_id, entry_date, rent_amount):
    """Generate payment history for a tenant"""
    payments = []
    today = datetime.now()
    current_date = entry_date
    
    # Generate payments from entry date to today
    current_date = entry_date
    
    while current_date <= today:
        # Generate a payment for each month
        payment_date = current_date + timedelta(days=random.randint(1, 5))  # Payment within 1-5 days of due date
        
        # Randomly skip some payments (10% chance)
        if random.random() > 0.1:
            # Random payment amount (80-120% of rent)
            amount = round(rent_amount * random.uniform(0.8, 1.2), 2)
            
            # Random status (85% completed, 10% pending, 5% other statuses)
            # Only use valid PaymentStatus enum values: PENDING, COMPLETED, CANCELLED, REFUNDED
            status_roll = random.random()
            if status_roll < 0.85:
                status = 'COMPLETED'
            elif status_roll < 0.95:
                status = 'PENDING'
            else:
                # Randomly choose between CANCELLED and REFUNDED for the remaining 5%
                status = random.choice(['CANCELLED', 'REFUNDED'])
            
            # Random payment type (80% rent, 10% deposit, 5% fine, 5% other)
            # Using the actual enum values to ensure case matches what the application expects
            payment_type_roll = random.random()
            if payment_type_roll < 0.8:
                payment_type = 'RENT'
            elif payment_type_roll < 0.9:
                payment_type = 'DEPOSIT'
            elif payment_type_roll < 0.95:
                payment_type = 'FINE'
            else:
                payment_type = 'OTHER'
            
            # Create payment record
            payment = {
                'tenant_id': tenant_id,
                'amount': amount,
                'payment_date': payment_date.strftime('%Y-%m-%d %H:%M:%S'),
                'payment_type': payment_type,
                'status': status,
                'reference_month': current_date.strftime('%Y-%m-01'),
                'description': f'Payment for {current_date.strftime("%B %Y")}',
                'created_at': payment_date.strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': payment_date.strftime('%Y-%m-%d %H:%M:%S')
            }
            payments.append(payment)
        
        # Move to next month
        if current_date.month == 12:
            current_date = current_date.replace(year=current_date.year + 1, month=1, day=1)
        else:
            current_date = current_date.replace(month=current_date.month + 1, day=1)
    
    return payments

# ... (rest of the code remains the same)

def create_test_database(db_path='test_tenants.db', num_tenants=50):
    """Create a test SQLite database with comprehensive test data"""
    # Remove existing database if it exists
    if os.path.exists(db_path):
        os.path.exists(db_path) and os.remove(db_path)
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Enable foreign key support
    cursor.execute('PRAGMA foreign_keys = ON')
    
    # Create all tables
    create_tables(cursor)
    
    print(f"Generating {num_tenants} test tenants...")
    
    # Generate tenants and their data
    for i in range(1, num_tenants + 1):
        # Generate tenant data
        tenant_data = generate_tenant_data()
        
        # Insert tenant
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
        INSERT INTO tenants (
            name, room, rent, bi, email, phone, address, 
            birth_date, entry_date, created_at, updated_at, is_active
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            tenant_data['name'],
            tenant_data['room'],
            tenant_data['rent'],
            tenant_data['bi'],
            tenant_data['email'],
            tenant_data['phone'],
            tenant_data['address'],
            tenant_data['birth_date'],
            tenant_data['entry_date'],
            current_time,
            current_time,
            tenant_data['is_active']
        ))
        
        tenant_id = cursor.lastrowid
        
        # Generate emergency contact (70% chance)
        if random.random() < 0.7:
            contact = generate_emergency_contact(tenant_id)
            cursor.execute('''
            INSERT INTO emergency_contacts (tenant_id, name, phone, email, relationship)
            VALUES (?, ?, ?, ?, ?)
            ''', (
                contact['tenant_id'],
                contact['name'],
                contact['phone'],
                contact['email'],
                contact['relationship']
            ))
        
        # Generate rent history
        entry_date = tenant_data['entry_date']
        if isinstance(entry_date, str):
            entry_date = datetime.strptime(entry_date, '%Y-%m-%d').date()
        entry_date = datetime.combine(entry_date, datetime.min.time())
        
        rent_histories = generate_rent_history(tenant_id, entry_date, tenant_data['rent'])
        for history in rent_histories:
            cursor.execute('''
            INSERT INTO rent_history (tenant_id, amount, valid_from, valid_to, changed_at, changed_by)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                history['tenant_id'],
                history['amount'],
                history['valid_from'],
                history['valid_to'],
                history['changed_at'],
                history['changed_by']
            ))
        
        # Generate payments
        payments = generate_payments(tenant_id, entry_date, tenant_data['rent'])
        for payment in payments:
            cursor.execute('''
            INSERT INTO payments (tenant_id, amount, payment_date, payment_type, status, reference_month, description, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                payment['tenant_id'],
                payment['amount'],
                payment['payment_date'],
                payment['payment_type'],
                payment['status'],
                payment['reference_month'],
                payment['description'],
                payment['created_at'],
                payment['updated_at']
            ))
        
        # Print progress
        if i % 10 == 0 or i == num_tenants:
            print(f"Generated {i}/{num_tenants} tenants...")
    
    # Create some special test cases
    create_special_test_cases(cursor)
    
    # Commit changes and close connection
    conn.commit()
    conn.close()
    
    print(f"\nSuccessfully created test database with {num_tenants} tenants at: {os.path.abspath(db_path)}")
    print("\nTest database includes:")
    print(f"- {num_tenants} tenants (with various statuses)")
    print("- Realistic payment histories (on-time, late, partial, missed)")
    print("- Rent history with increases over time")
    print("- Emergency contacts for most tenants")
    print("\nYou can now use this database file with your application.")

def create_special_test_cases(cursor):
    """Create some special test cases for edge scenarios"""
    print("\nCreating special test cases...")
    
    # 1. Tenant with very long name and special characters
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''
    INSERT INTO tenants (
        name, room, rent, bi, email, phone, address, 
        birth_date, entry_date, created_at, updated_at, is_active
    ) VALUES (?, '1X', 500.00, '12345678', 'long.name@example.com', '912345678', 
    'Rua do Teste Longo com caracteres especiais çãõé, 123, 4º D, 1000-001 Lisboa',
    '1980-01-01', '2020-01-01', ?, ?, 1)
    ''', ('João Carlos dos Santos e Silva Gonçalves de Almeida d\'Ávila', current_time, current_time))
    
    tenant_id = cursor.lastrowid
    
    # Add emergency contact
    cursor.execute('''
    INSERT INTO emergency_contacts (tenant_id, name, phone, email, relationship)
    VALUES (?, 'Maria dos Santos Silva', '912345679', 'maria.silva@example.com', 'Mother')
    ''', (tenant_id,))
    
    # 2. Tenant with zero rent (free accommodation)
    cursor.execute('''
    INSERT INTO tenants (
        name, room, rent, bi, email, phone, address, 
        birth_date, entry_date, created_at, updated_at, is_active
    ) VALUES ('Ana Zero', '2X', 0.00, '87654321', 'ana.zero@example.com', '912345677', 
    'Rua do Zero, 0, 1000-002 Lisboa', '1990-05-15', '2021-06-01', ?, ?, 1)
    ''', (current_time, current_time))
    
    # 3. Tenant with very high rent
    cursor.execute('''
    INSERT INTO tenants (
        name, room, rent, bi, email, phone, address, 
        birth_date, entry_date, created_at, updated_at, is_active
    ) VALUES ('Carlos Rico', 'PH', 5000.00, '11223344', 'carlos.rico@example.com', '912345676', 
    'Avenida da Liberdade, 200, 1250-001 Lisboa', '1975-11-30', '2019-03-15', ?, ?, 1)
    ''', (current_time, current_time))
    
    tenant_id = cursor.lastrowid
    
    # Add rent history for high rent tenant
    cursor.execute('''
    INSERT INTO rent_history (tenant_id, amount, valid_from, valid_to, changed_at, changed_by)
    VALUES (?, 4500.00, '2019-03-15', '2022-01-01', '2019-03-15', 'system')
    ''', (tenant_id,))
    
    cursor.execute('''
    INSERT INTO rent_history (tenant_id, amount, valid_from, changed_at, changed_by)
    VALUES (?, 5000.00, '2022-01-01', '2022-01-01', 'system')
    ''', (tenant_id,))
    
    print("Created special test cases for edge scenarios")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate a test database for the Tenants Manager application')
    parser.add_argument('--db', default='test_tenants.db', help='Path to the SQLite database file')
    parser.add_argument('--tenants', type=int, default=50, help='Number of tenants to generate')
    
    args = parser.parse_args()
    
    try:
        create_test_database(args.db, args.tenants)
    except Exception as e:
        print(f"Error creating test database: {e}", file=sys.stderr)
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
