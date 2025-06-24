import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Base directory
BASE_DIR = Path(__file__).parent.parent.parent
LOG_DIR = BASE_DIR / 'logs'

# Ensure logs directory exists
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Set up file logging
# Configure database logging to be less verbose
logging.basicConfig(
    level=logging.WARNING,  # Changed from DEBUG to WARNING
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / 'database.log', mode='a'),  # Changed to append mode
    ]
)
logger = logging.getLogger(__name__)

# Also log to console for critical errors
console = logging.StreamHandler()
console.setLevel(logging.ERROR)
formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

# Load environment variables from .env file
try:
    load_dotenv()
    logger.info("Loaded environment variables")
except Exception as e:
    logging.error(f"Error loading .env file: {e}")
    raise

# Base directory
BASE_DIR = Path(__file__).parent.parent.parent
logger.info(f"Base directory: {BASE_DIR}")

# Database environment (dev, test, prod)
DB_ENV = os.getenv('DB_ENV', 'dev').lower()
logger.info(f"Database environment: {DB_ENV}")

# Database paths
DB_PATHS = {
    'dev': BASE_DIR / 'data' / 'dev' / 'tenants.db',
    'test': BASE_DIR / 'data' / 'test' / 'tenants.db',
    'prod': BASE_DIR / 'data' / 'prod' / 'tenants.db',
}

def get_database_url() -> str:
    """Get the database URL based on the current environment."""
    try:
        # Get the path for the current environment
        db_path = DB_PATHS.get(DB_ENV, DB_PATHS['dev'])
        logger.info(f"Selected database path for environment '{DB_ENV}': {db_path}")
        
        # Convert to absolute path and normalize
        db_path = db_path.absolute()
        logger.info(f"Absolute database path: {db_path}")
        
        # Create parent directories if they don't exist
        db_dir = db_path.parent
        logger.info(f"Database directory: {db_dir}")
        logger.info(f"Directory exists: {db_dir.exists()}")
        
        if not db_dir.exists():
            logger.info(f"Creating directory: {db_dir}")
            db_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Directory created: {db_dir.exists()}")
        
        # Format the URL with forward slashes for SQLAlchemy
        url = f'sqlite:///{db_path}'.replace('\\', '/')
        logger.info(f"Final database URL: {url}")
        return url
        
    except Exception as e:
        logger.exception("Error getting database URL:")
        raise

def get_migrations_dir() -> Path:
    """Get the path to the migrations directory."""
    try:
        migrations_dir = BASE_DIR / 'data' / 'migrations'
        logger.info(f"Migrations directory: {migrations_dir}")
        
        # Create migrations directory if it doesn't exist
        if not migrations_dir.exists():
            logger.info("Creating migrations directory")
            migrations_dir.mkdir(parents=True, exist_ok=True)
            
        return migrations_dir
    except Exception as e:
        logger.exception("Error getting migrations directory:")
        raise
