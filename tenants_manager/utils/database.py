import os
import sys
from sqlalchemy import create_engine, func, and_, or_
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime, date

# Enable debug logging
debug = True

def debug_log(*args, **kwargs):
    """Print debug messages if debug is enabled."""
    if debug:
        print("[DB_DEBUG]", *args, file=sys.stderr, **kwargs)

from ..models.tenant import Base, Tenant, EmergencyContact, Payment, RentHistory, PaymentStatus, PaymentType
from ..config.database import get_database_url, get_migrations_dir

class DatabaseManager:
    def __init__(self, db_url=None):
        """Initialize the database manager.
        
        Args:
            db_url: Optional database URL. If not provided, uses the URL from config.
        """
        debug_log("Initializing DatabaseManager")
        self.db_url = db_url or get_database_url()
        debug_log(f"Database URL: {self.db_url}")
        
        try:
            debug_log("Creating SQLAlchemy engine...")
            self.engine = create_engine(self.db_url, echo=True)  # Enable SQL echo for debugging
            debug_log("Engine created successfully")
            
            debug_log("Creating session maker...")
            self.Session = sessionmaker(bind=self.engine)
            debug_log("Session maker created successfully")
            
            # Initialize the database schema if needed
            debug_log("Initializing database...")
            self.initialize_database()
            debug_log("Database initialization complete")
            
        except Exception as e:
            debug_log(f"Error initializing database: {str(e)}")
            debug_log(f"Database URL was: {self.db_url}")
            raise
    
    def initialize_database(self):
        """Initialize the database by creating all tables."""
        debug_log("Creating database tables...")
        try:
            Base.metadata.create_all(self.engine)
            debug_log("Database tables created successfully")
            
            # Verify the database file was created
            if 'sqlite' in self.db_url:
                db_path = self.db_url.replace('sqlite:///', '')
                debug_log(f"Checking if database file exists at: {db_path}")
                if os.path.exists(db_path):
                    debug_log("Database file exists")
                else:
                    debug_log("WARNING: Database file was not created!")
        except Exception as e:
            debug_log(f"Error creating database tables: {str(e)}")
            raise

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

    def get_tenants_count(self, search_term=None, include_deleted=False):
        """Get the total count of tenants, optionally filtered by search term"""
        print(f"\n=== get_tenants_count(search_term='{search_term}', include_deleted={include_deleted}) ===")
        
        with self.Session() as session:
            try:
                if include_deleted:
                    query = session.query(func.count(Tenant.id))
                else:
                    query = session.query(func.count(Tenant.id)).filter(Tenant.is_active == True)
                
                if search_term and search_term.strip():
                    search = f"%{search_term}%"
                    query = query.filter(Tenant.name.ilike(search))
                
                count = query.scalar() or 0
                print(f"Found {count} tenants matching criteria")
                return count
                
            except Exception as e:
                print(f"Error getting tenant count: {str(e)}")
                import traceback
                traceback.print_exc()
                return 0
    
    def get_tenants_paginated(self, offset=0, limit=20, search_term=None, include_deleted=False):
        """Get a paginated list of tenants"""
        print(f"\n=== get_tenants_paginated(offset={offset}, limit={limit}, search_term='{search_term}', include_deleted={include_deleted}) ===")
        
        with self.Session() as session:
            try:
                if include_deleted:
                    query = session.query(Tenant)
                else:
                    query = session.query(Tenant).filter(Tenant.is_active == True)
                
                if search_term and search_term.strip():
                    search = f"%{search_term}%"
                    query = query.filter(Tenant.name.ilike(search))
                
                tenants = query.order_by(Tenant.name).offset(offset).limit(limit).all()
                print(f"Retrieved {len(tenants)} tenants")
                
                # Print first few tenants for debugging
                max_print = min(3, len(tenants))
                for i in range(max_print):
                    print(f"  {i+1}. {tenants[i].name} (ID: {tenants[i].id})")
                if len(tenants) > max_print:
                    print(f"  ... and {len(tenants) - max_print} more")
                
                return tenants
                
            except Exception as e:
                print(f"Error getting paginated tenants: {str(e)}")
                import traceback
                traceback.print_exc()
                return []
    
    def get_tenants(self, page=1, per_page=20, search_term=None, include_inactive=False):
        """Get paginated list of tenants from the database (legacy method)"""
        print(f"\n=== get_tenants(page={page}, per_page={per_page}, search_term='{search_term}', include_inactive={include_inactive}) ===")
        
        # Get the total count
        total = self.get_tenants_count(search_term, include_inactive)
        
        # Get paginated results
        offset = (page - 1) * per_page
        tenants = self.get_tenants_paginated(offset, per_page, search_term, include_inactive)
        
        return tenants, total
    
    def get_session(self):
        return self.Session()
        
    def delete_tenant(self, tenant_id, hard_delete=False):
        """Delete a tenant, with option for hard or soft delete.
        
        Args:
            tenant_id (int): The ID of the tenant to delete
            hard_delete (bool): If True, permanently delete the tenant. 
                             If False (default), perform a soft delete.
            
        Returns:
            bool: True if the tenant was successfully deleted, False otherwise
        """
        with self.Session() as session:
            try:
                # Get the tenant
                tenant = session.query(Tenant).get(tenant_id)
                if not tenant:
                    print(f"Error: No tenant found with ID {tenant_id}")
                    return False
                
                if hard_delete:
                    # Hard delete - remove the tenant completely
                    session.delete(tenant)
                    action = "hard-deleted"
                else:
                    # Soft delete - mark as inactive
                    tenant.soft_delete()
                    action = "soft-deleted"
                
                session.commit()
                print(f"Successfully {action} tenant ID {tenant_id}")
                return True
                
            except Exception as e:
                session.rollback()
                print(f"Error deleting tenant ID {tenant_id}: {str(e)}")
                import traceback
                traceback.print_exc()
                return False
                
    def restore_tenant(self, tenant_id):
        """Restore a soft-deleted tenant.
        
        Args:
            tenant_id (int): The ID of the tenant to restore
            
        Returns:
            bool: True if the tenant was successfully restored, False otherwise
        """
        with self.Session() as session:
            try:
                # Get the tenant, including soft-deleted ones
                tenant = session.query(Tenant).filter_by(id=tenant_id).first()
                if not tenant:
                    print(f"Error: No tenant found with ID {tenant_id}")
                    return False
                    
                # Restore the tenant
                tenant.restore()
                session.commit()
                print(f"Successfully restored tenant ID {tenant_id}")
                return True
                
            except Exception as e:
                session.rollback()
                print(f"Error restoring tenant ID {tenant_id}: {str(e)}")
                import traceback
                traceback.print_exc()
                return False
        
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
            # Base query for actual payments
            query = session.query(Payment).filter(Payment.tenant_id == tenant_id)
            
            # Apply date filters to actual payments
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
            actual_payments = query.order_by(Payment.payment_date.desc()).all()
            payments = list(actual_payments)  # Create a copy to avoid modifying the original
            
            # If we should include expected rent entries
            if include_expected and (start_date and end_date) and not reference_month:
                # Get expected rent entries for the date range
                expected_entries = self.get_expected_rent_entries(tenant_id, start_date, end_date)
                
                # Convert actual payments to dict format for easier comparison
                actual_payments_dict = {}
                for payment in actual_payments:
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
                
                # Sort all payments by reference month in descending order (newest first)
                payments.sort(
                    key=lambda p: (
                        getattr(p, 'reference_month', None) or 
                        getattr(p, 'payment_date', None) or 
                        datetime.min
                    ),
                    reverse=True
                )
            
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
