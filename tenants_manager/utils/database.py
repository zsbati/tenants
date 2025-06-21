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

    def get_tenants(self, page=1, per_page=20, search_term=None, include_inactive=False):
        """Get paginated list of tenants from the database
        
        Args:
            page (int): Page number (1-based)
            per_page (int): Number of items per page
            search_term (str, optional): Optional search term to filter tenants by name
            include_inactive (bool, optional): If True, includes soft-deleted tenants
            
        Returns:
            tuple: (list_of_tenants, total_count)
        """
        print(f"\n=== get_tenants(page={page}, per_page={per_page}, search_term='{search_term}', include_inactive={include_inactive}) ===")
        
        with self.Session() as session:
            try:
                print("Creating base query...")
                if include_inactive:
                    query = session.query(Tenant)
                else:
                    query = Tenant.query_active(session)
                print(f"Base query created. Query: {query}")
                
                # Apply search filter if provided
                if search_term and search_term.strip():
                    print(f"Applying search filter for: {search_term}")
                    search = f"%{search_term}%"
                    query = query.filter(Tenant.name.ilike(search))
                
                # Get total count for pagination
                print("Counting total tenants...")
                total = query.count()
                print(f"Total tenants: {total}")
                
                # Apply pagination and order by name for consistent results
                offset = (page - 1) * per_page
                print(f"Fetching tenants (offset={offset}, limit={per_page})...")
                tenants = query.order_by(Tenant.name).offset(offset).limit(per_page).all()
                print(f"Retrieved {len(tenants)} tenant(s)")
                
                # Debug: Print all tenants
                print("\nTenants retrieved:")
                for i, tenant in enumerate(tenants, 1):
                    print(f"  {i}. ID: {getattr(tenant, 'id', 'N/A')}, Name: {getattr(tenant, 'name', 'N/A')}, Type: {type(tenant)}")
                
                # Log any invalid tenant objects for debugging
                invalid_tenants = [t for t in tenants if not hasattr(t, 'id')]
                if invalid_tenants:
                    print(f"\nWarning: Found {len(invalid_tenants)} invalid tenant objects:")
                    for i, t in enumerate(invalid_tenants, 1):
                        print(f"  {i}. Type: {type(t)}, Content: {t}")
                
                # Filter out invalid tenants
                valid_tenants = [t for t in tenants if hasattr(t, 'id')]
                print(f"\nReturning {len(valid_tenants)} valid tenant(s)")
                
                return valid_tenants, total
                
            except Exception as e:
                print(f"\n!!! ERROR in get_tenants: {str(e)}")
                import traceback
                traceback.print_exc()
                print("Returning empty list due to error")
                return [], 0
    
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
    
    def get_tenant_payments(self, tenant_id, start_date=None, end_date=None, reference_month=None, 
                       page=1, per_page=20, search_term=None, include_expected=True):
        """Get paginated payments for a tenant with optional filters
        
        Args:
            tenant_id (int): ID of the tenant
            start_date (date, optional): Filter payments after this date
            end_date (date, optional): Filter payments before this date
            reference_month (date, optional): Filter payments for a specific month
            page (int): Page number (1-based)
            per_page (int): Number of items per page
            search_term (str, optional): Optional search term to filter payments by description
            include_expected (bool): Whether to include expected rent entries for months without payments
            
        Returns:
            tuple: (list_of_payments, total_count)
        """
        with self.Session() as session:
            # Base query
            query = session.query(Payment).filter(Payment.tenant_id == tenant_id)
            
            # Apply date filters
            if start_date:
                query = query.filter(Payment.payment_date >= start_date)
            if end_date:
                # Include the entire end date
                end_of_day = datetime.combine(end_date, datetime.max.time())
                query = query.filter(Payment.payment_date <= end_of_day)
            if reference_month:
                # If reference_month is provided, filter payments for that specific month
                query = query.filter(
                    func.strftime('%Y-%m', Payment.reference_month) == reference_month.strftime('%Y-%m')
                )
            
            # Apply search term if provided
            if search_term and search_term.strip():
                search = f"%{search_term.strip()}%"
                query = query.filter(
                    or_(
                        Payment.description.ilike(search),
                        Payment.payment_type.ilike(search),
                        Payment.status.ilike(search)
                    )
                )
            
            # Get actual payments
            payments = query.order_by(Payment.payment_date.desc()).all()
            
            # If we should include expected rent entries
            if include_expected and (start_date and end_date) and not reference_month:
                # Get expected rent entries for the date range
                expected_entries = self.get_expected_rent_entries(tenant_id, start_date, end_date)
                
                # Convert actual payments to dict format for easier comparison
                actual_payments_dict = {}
                for payment in payments:
                    if payment.reference_month:
                        month_key = payment.reference_month.strftime('%Y-%m')
                        actual_payments_dict[month_key] = payment
                
                # Add expected entries for months without actual payments
                for entry in expected_entries:
                    month_key = entry['reference_month'].strftime('%Y-%m')
                    if month_key not in actual_payments_dict:
                        # Create a Payment-like object for the expected entry
                        payment = type('Payment', (), entry)
                        payments.append(payment)
            
            # Apply pagination
            total = len(payments)
            offset = (page - 1) * per_page
            paginated_payments = payments[offset:offset + per_page]
            
            return paginated_payments, total
            
    def get_expected_rent_entries(self, tenant_id, start_date, end_date):
        """Generate expected rent entries for a tenant between two dates"""
        with self.Session() as session:
            # Get the tenant's rent history
            tenant = session.query(Tenant).get(tenant_id)
            if not tenant:
                return []
                
            # Get all rent history records in chronological order
            history = sorted(tenant.rent_history, key=lambda x: x.valid_from)
            
            # If no rent history, use current rent
            if not history:
                entry_date = tenant.entry_date.date() if hasattr(tenant.entry_date, 'date') else tenant.entry_date
                history = [type('obj', (object,), {'valid_from': entry_date or datetime.min, 'amount': tenant.rent})]
            
            # Generate expected rent for each month in the date range
            expected_entries = []
            current_date = max(start_date, tenant.entry_date.date() if hasattr(tenant.entry_date, 'date') else tenant.entry_date)
            
            # Ensure end_date is a date object
            if hasattr(end_date, 'date'):
                end_date = end_date.date()
            
            while current_date <= end_date:
                # Find the applicable rent for the current date
                applicable_rent = tenant.rent  # Default to current rent
                
                for record in history:
                    valid_from = record.valid_from.date() if hasattr(record.valid_from, 'date') else record.valid_from
                    if valid_from <= current_date:
                        applicable_rent = record.amount
                    else:
                        break
                
                # Create an expected rent entry for this month if there's no actual payment
                # Check if we have a payment for this month
                current_month_str = current_date.strftime('%Y-%m')
                has_payment = session.query(Payment).filter(
                    Payment.tenant_id == tenant_id,
                    Payment.payment_type == PaymentType.RENT,
                    func.strftime('%Y-%m', Payment.reference_month) == current_month_str
                ).first() is not None
                
                if not has_payment and applicable_rent > 0:
                    # Create a date object for the first day of the month
                    month_date = current_date.replace(day=1)
                    if hasattr(month_date, 'date'):
                        month_date = month_date.date()
                    
                    expected_entries.append({
                        'id': None,
                        'tenant_id': tenant_id,
                        'payment_date': None,
                        'amount': float(applicable_rent),  # Ensure it's a float
                        'payment_type': PaymentType.RENT,
                        'reference_month': month_date,
                        'description': f'Renda esperada para {current_date.strftime("%B %Y")}',
                        'status': 'EXPECTED',
                        'is_expected': True,
                        'created_at': datetime.now(),
                        'updated_at': datetime.now()
                    })
                
                # Move to the first day of the next month
                try:
                    if current_date.month == 12:
                        current_date = current_date.replace(year=current_date.year + 1, month=1, day=1)
                    else:
                        current_date = current_date.replace(month=current_date.month + 1, day=1)
                    
                    # Ensure current_date is a date object for the next iteration
                    if hasattr(current_date, 'date') and not isinstance(current_date, datetime.date):
                        current_date = current_date.date()
                except ValueError as e:
                    # Handle invalid date (e.g., Feb 30)
                    if current_date.month == 12:
                        current_date = current_date.replace(year=current_date.year + 1, month=1, day=1)
                    else:
                        current_date = current_date.replace(month=current_date.month + 2, day=1)
                    if hasattr(current_date, 'date'):
                        current_date = current_date.date()
            
            return expected_entries

    def get_total_rent_collected(self, reference_month=None):
        """Get total rent collected for a specific month"""
        if reference_month is None:
            reference_month = datetime.utcnow()
            
        with self.Session() as session:
            total = session.query(
                func.sum(Payment.amount)
            ).filter(
                Payment.payment_type == PaymentType.RENT,
                Payment.status == PaymentStatus.COMPLETED,
                func.strftime('%Y-%m', Payment.reference_month) == reference_month.strftime('%Y-%m')
            ).scalar()
            
            return total or 0.0
    
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
        try:
            if as_of_date is None:
                as_of_date = datetime.utcnow()
                
            print(f"Getting balance for tenant_id: {tenant_id}, type: {type(tenant_id)}")
            
            with self.Session() as session:
                # Ensure tenant_id is an integer
                try:
                    if isinstance(tenant_id, (list, tuple)) and len(tenant_id) > 0:
                        tenant_id = tenant_id[0]  # Take first item if it's a list
                    tenant_id = int(tenant_id)  # Ensure it's an integer
                except (ValueError, TypeError) as e:
                    print(f"Error converting tenant_id to int: {e}, type: {type(tenant_id)}")
                    return 0.0
                
                tenant = session.query(Tenant).get(tenant_id)
                if not tenant:
                    print(f"No tenant found with id: {tenant_id}")
                    return 0.0
                
                print(f"Found tenant: ID={tenant.id}, Name={getattr(tenant, 'name', 'N/A')}")
                return tenant.get_balance(as_of_date)
                
        except Exception as e:
            print(f"Error in get_tenant_balance: {str(e)}")
            import traceback
            traceback.print_exc()
            return 0.0
    
    def get_total_debt(self, as_of_date=None):
        """Calculate the total debt across all tenants (sum of positive balances)"""
        if as_of_date is None:
            as_of_date = datetime.utcnow()
            
        total_debt = 0.0
        with self.Session() as session:
            tenants = session.query(Tenant).all()
            for tenant in tenants:
                balance = tenant.get_balance(as_of_date)
                if balance > 0:  # Only count positive balances (debts)
                    total_debt += balance
        return total_debt
    
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
