# Testing Tools for Tenants Manager

This directory contains tools for generating test data and running performance tests for the Tenants Manager application.

## Setup

1. Install the required dependencies:
   ```bash
   pip install faker
   ```

2. Create a backup of your production database before running any tests.

## Test Data Generation

The `generate_test_data.py` script generates realistic test data for the application.

### Usage

```bash
# Generate 100 test tenants (default)
python -m tests.generate_test_data

# Generate a specific number of test tenants (e.g., 500)
python -m tests.generate_test_data 500
```

### What it generates:
- Random tenants with realistic Portuguese names and contact information
- Emergency contacts for active tenants
- Rent history with realistic changes over time
- Payment history with some random missed or partial payments

## Performance Testing

The `performance_tests.py` script runs various performance tests on the application.

### Usage

```bash
python -m tests.performance_tests
```

### Tests included:
1. **Tenant Listing** - Tests pagination performance
2. **Tenant Search** - Tests search functionality with different terms
3. **Payment Reporting** - Tests reporting queries for payment data
4. **Rent Calculation** - Tests the performance of rent balance calculations

## Running Tests on a Copy of Production Data

1. Create a copy of your production database:
   ```bash
   cp tenants.db test_tenants.db
   ```

2. Update the database URL in the test scripts if needed (default is SQLite in the project root).

3. Run the performance tests:
   ```bash
   python -m tests.performance_tests
   ```

## Analyzing Results

- Look for queries that take longer than 100ms as potential performance bottlenecks
- Pay attention to the rent calculation times as these can become slow with many transactions
- Consider adding database indexes for frequently queried columns

## Tips for Testing Large Datasets

1. Start with a small number of tenants (e.g., 100) and gradually increase
2. Monitor memory usage when generating large datasets
3. Consider running tests on a machine with similar specifications to production
4. Use the performance test results to identify and optimize slow queries
