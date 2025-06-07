import os
import sys
import pathlib

# Add the project root to Python path
project_root = pathlib.Path(__file__).parent
sys.path.insert(0, str(project_root))

from tenants_manager.main import main

if __name__ == "__main__":
    main()
