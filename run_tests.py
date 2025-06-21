import sys
import subprocess
import os

def check_environment():
    print("=== Python Environment Check ===")
    print(f"Python executable: {sys.executable}")
    print(f"Python version: {sys.version}")
    print(f"Current working directory: {os.getcwd()}")
    print("\n=== Installed Packages ===")
    subprocess.run([sys.executable, "-m", "pip", "list"], check=True)

def run_test_data_generator(num_tenants=50):
    print(f"\n=== Generating Test Data for {num_tenants} Tenants ===")
    try:
        # Add current directory to path
        sys.path.insert(0, os.getcwd())
        
        # Import and run the test data generator
        from tests.generate_test_data import generate_test_data
        generate_test_data(num_tenants)
        print("\n=== Test Data Generation Completed Successfully ===")
    except Exception as e:
        print(f"\n=== Error Running Test Data Generator ===")
        print(f"Error type: {type(e).__name__}")
        print(f"Error details: {str(e)}")
        print("\nMake sure you have installed all required dependencies:")
        print("pip install -r requirements-test.txt")
        
        # Print Python path for debugging
        print("\n=== Python Path ===")
        for path in sys.path:
            print(f"- {path}")

if __name__ == "__main__":
    check_environment()
    run_test_data_generator(50)
