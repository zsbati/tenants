import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import and run the test data generator
from tests.generate_test_data import generate_test_data

if __name__ == "__main__":
    # Generate 100 test tenants
    num_tenants = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    print(f"Generating test data for {num_tenants} tenants...")
    generate_test_data(num_tenants)
