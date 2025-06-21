import time
import random
from datetime import datetime, timedelta
from sqlalchemy import func, and_
from tenants_manager.models.tenant import Tenant, Payment, RentHistory
from tenants_manager.utils.database import DatabaseManager
import statistics
import os
import sys

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class PerformanceTester:
    def __init__(self):
        self.db = DatabaseManager()
        self.session = self.db.get_session()
    
    def measure_query_time(self, query_func, *args, **kwargs):
        """Measure the execution time of a query function"""
        start_time = time.time()
        result = query_func(*args, **kwargs)
        end_time = time.time()
        return end_time - start_time, result
    
    def test_get_tenants_pagination(self, page_size=20):
        """Test performance of tenant listing with pagination"""
        print("\n=== Testing tenant listing with pagination ===")
        
        # Get total count
        total_tenants = self.session.query(Tenant).count()
        print(f"Total tenants in database: {total_tenants}")
        
        # Test with different page sizes
        for page in range(1, 6):
            offset = (page - 1) * page_size
            
            def query():
                return self.session.query(Tenant)\
                    .filter(Tenant.is_active == True)\
                    .order_by(Tenant.name)\
                    .offset(offset)\
                    .limit(page_size)\
                    .all()
            
            time_taken, _ = self.measure_query_time(query)
            print(f"Page {page} (offset={offset}, limit={page_size}): {time_taken:.4f} seconds")
    
    def test_tenant_search(self, search_terms):
        """Test performance of tenant search"""
        print("\n=== Testing tenant search performance ===")
        
        for term in search_terms:
            def query():
                return self.session.query(Tenant)\
                    .filter(Tenant.name.ilike(f"%{term}%"))\
                    .limit(50)\
                    .all()
            
            time_taken, results = self.measure_query_time(query)
            print(f"Search for '{term}': {len(results)} results in {time_taken:.4f} seconds")
    
    def test_payment_reporting(self, start_date, end_date):
        """Test performance of payment reporting"""
        print("\n=== Testing payment reporting performance ===")
        
        # Total payments in date range
        def total_payments_query():
            return self.session.query(func.sum(Payment.amount))\
                .filter(Payment.payment_date.between(start_date, end_date))\
                .scalar() or 0
        
        time_taken, total = self.measure_query_time(total_payments_query)
        print(f"Total payments ({start_date} to {end_date}): €{total:.2f} in {time_taken:.4f} seconds")
        
        # Payments by month
        def monthly_payments_query():
            return self.session.query(
                    func.strftime('%Y-%m', Payment.payment_date).label('month'),
                    func.sum(Payment.amount).label('total')
                )\
                .filter(Payment.payment_date.between(start_date, end_date))\
                .group_by('month')\
                .order_by('month')\
                .all()
        
        time_taken, results = self.measure_query_time(monthly_payments_query)
        print(f"Monthly breakdown ({len(results)} months) in {time_taken:.4f} seconds")
    
    def test_rent_calculation(self, sample_size=100):
        """Test performance of rent calculation for tenants"""
        print("\n=== Testing rent calculation performance ===")
        
        # Get a sample of tenants
        tenant_ids = [id[0] for id in self.session.query(Tenant.id).limit(sample_size).all()]
        times = []
        
        for tenant_id in tenant_ids:
            def query():
                return self.session.query(Tenant).get(tenant_id)
            
            time_taken, tenant = self.measure_query_time(query)
            
            # Time the balance calculation
            start_time = time.time()
            balance = tenant.get_balance()
            end_time = time.time()
            
            calc_time = end_time - start_time
            times.append(calc_time)
            
            print(f"Tenant {tenant_id}: balance=€{balance:.2f}, calculation time: {calc_time:.4f} seconds")
        
        if times:
            print(f"\nRent calculation statistics (n={len(times)}):")
            print(f"  Min: {min(times):.4f}s")
            print(f"  Max: {max(times):.4f}s")
            print(f"  Avg: {statistics.mean(times):.4f}s")
            print(f"  P95: {statistics.quantiles(times, n=20)[-1]:.4f}s")
    
    def run_all_tests(self):
        """Run all performance tests"""
        print("=== Starting Performance Tests ===")
        
        # Test data
        search_terms = ['a', 'e', 'da', 'os', 'silva']
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)  # Last year
        
        # Run tests
        self.test_get_tenants_pagination()
        self.test_tenant_search(search_terms)
        self.test_payment_reporting(start_date, end_date)
        self.test_rent_calculation()
        
        print("\n=== Performance Tests Complete ===")

if __name__ == "__main__":
    tester = PerformanceTester()
    tester.run_all_tests()
