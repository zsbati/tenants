from sqlalchemy import create_engine, func, and_, or_
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime, date
from ..models.tenant import Base, Tenant, EmergencyContact, Payment, RentHistory, PaymentStatus, PaymentType
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
                tenants = session.query(Tenant).all()
                return tenants
            except Exception as e:
                print(f"Error getting tenants: {str(e)}")
                return []
    
    def get_session(self):
        return self.Session()
        
    def record_payment(self, tenant_id, amount, payment_date=None, payment_type=PaymentType.RENT, 
                       reference_month=None, description=None, status=PaymentStatus.COMPLETED):
        """Record a payment for a tenant"""
        if payment_date is None:
            payment_date = datetime.utcnow()
            
        if reference_month is None:
            reference_month = date.today().replace(day=1)
        elif isinstance(reference_month, date):
            reference_month = reference_month.replace(day=1)
            
        payment = Payment(
            tenant_id=tenant_id,
            amount=amount,
            payment_date=payment_date,
            payment_type=payment_type,
            reference_month=reference_month,
            description=description,
            status=status
        )
        
        with self.Session() as session:
            try:
                session.add(payment)
                session.commit()
                return payment
            except Exception as e:
                session.rollback()
                print(f"Error recording payment: {str(e)}")
                return None
    
    def get_tenant_payments(self, tenant_id, start_date=None, end_date=None, reference_month=None):
        """Get all payments for a tenant within a date range or for a specific reference month"""
        with self.Session() as session:
            query = session.query(Payment).filter(Payment.tenant_id == tenant_id)
            
            if start_date:
                query = query.filter(Payment.payment_date >= start_date)
            if end_date:
                query = query.filter(Payment.payment_date <= end_date)
            if reference_month:
                # If reference_month is provided, filter payments for that specific month
                query = query.filter(
                    func.strftime('%Y-%m', Payment.reference_month) == reference_month.strftime('%Y-%m')
                )
                
            return query.order_by(Payment.payment_date.desc()).all()
    
    def get_rent_history(self, tenant_id, start_date=None, end_date=None):
        """Get rent history for a tenant within a date range"""
        with self.Session() as session:
            query = session.query(RentHistory).filter(RentHistory.tenant_id == tenant_id)
            
            if start_date:
                query = query.filter(
                    or_(
                        RentHistory.valid_to >= start_date,
                        RentHistory.valid_to.is_(None)
                    )
                )
            if end_date:
                query = query.filter(RentHistory.valid_from <= end_date)
                
            return query.order_by(RentHistory.valid_from.desc()).all()
    
    def get_tenant_balance(self, tenant_id, as_of_date=None):
        """Get the current balance (rent due - payments) for a tenant"""
        if as_of_date is None:
            as_of_date = datetime.utcnow()
            
        with self.Session() as session:
            tenant = session.query(Tenant).get(tenant_id)
            if not tenant:
                return 0.0
                
            return tenant.get_balance(as_of_date)
    
    def generate_rent_statement(self, tenant_id, start_date, end_date=None):
        """Generate a rent statement for a tenant"""
        if end_date is None:
            end_date = datetime.utcnow()
            
        with self.Session() as session:
            tenant = session.query(Tenant).get(tenant_id)
            if not tenant:
                return None
                
            # Get all rent periods in the date range
            rent_periods = [
                period for period in tenant._get_rent_periods(end_date)
                if start_date <= period['date'] <= end_date
            ]
            
            # Get all payments in the date range
            payments = [
                payment for payment in tenant.payments
                if start_date <= payment.payment_date <= end_date
            ]
            
            # Calculate running balance
            running_balance = 0
            statement = {
                'tenant': tenant,
                'start_date': start_date,
                'end_date': end_date,
                'rent_charges': [],
                'payments': [],
                'opening_balance': 0,
                'closing_balance': 0,
                'total_rent_due': 0,
                'total_payments': 0
            }
            
            # Calculate opening balance (balance before start_date)
            statement['opening_balance'] = tenant.get_balance(start_date)
            running_balance = statement['opening_balance']
            
            # Add rent charges
            for period in rent_periods:
                statement['total_rent_due'] += period['amount']
                running_balance += period['amount']
                statement['rent_charges'].append({
                    'date': period['date'],
                    'amount': period['amount'],
                    'balance': running_balance,
                    'type': 'rent'
                })
            
            # Add payments
            for payment in payments:
                if payment.status == PaymentStatus.COMPLETED:
                    statement['total_payments'] += payment.amount
                    running_balance -= payment.amount
                    statement['payments'].append({
                        'date': payment.payment_date,
                        'amount': -payment.amount,  # Negative because it reduces the balance
                        'balance': running_balance,
                        'type': 'payment',
                        'reference': payment.reference_month.strftime('%Y-%m') if payment.reference_month else '',
                        'description': payment.description or ''
                    })
            
            statement['closing_balance'] = running_balance
            return statement
