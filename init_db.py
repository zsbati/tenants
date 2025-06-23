import os
import sys
import logging
from pathlib import Path

def setup_logging():
    """Set up file-based logging for the initialization script."""
    # Create logs directory if it doesn't exist
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    
    # Configure root logger
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / 'init_db.log', mode='w'),
        ]
    )
    
    # Also log errors to console
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(levelname)-8s %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)
    
    return logging.getLogger(__name__)

def main():
    logger = setup_logging()
    logger.info("=== Database Initialization Started ===")
    
    try:
        # Add project root to Python path
        project_root = Path(__file__).parent.absolute()
        sys.path.append(str(project_root))
        logger.info(f"Project root: {project_root}")
        
        # Import after setting up paths
        from tenants_manager.utils.database import DatabaseManager
        from tenants_manager.config.database import get_database_url, DB_ENV
        
        # Get the database URL from configuration
        logger.info(f"Using database environment: {DB_ENV}")
        db_url = get_database_url()
        logger.info(f"Database URL: {db_url}")
        
        # Create the database manager and initialize the database
        logger.info("Creating database manager...")
        manager = DatabaseManager(db_url=db_url)
        
        # Verify database file was created
        if 'sqlite' in db_url:
            db_path = db_url.replace('sqlite:///', '')
            if os.path.exists(db_path):
                logger.info(f"Database file created at: {db_path}")
                logger.info(f"File size: {os.path.getsize(db_path)} bytes")
                
                # Check if tables were created
                try:
                    import sqlite3
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                    tables = cursor.fetchall()
                    logger.info(f"Tables in database: {[t[0] for t in tables]}")
                    cursor.close()
                    conn.close()
                except Exception as e:
                    logger.error(f"Error checking database: {e}")
            else:
                logger.error(f"Database file was not created at: {db_path}")
                return 1
        
        logger.info("=== Database Initialization Completed Successfully ===")
        return 0
        
    except Exception as e:
        logger.exception("Error initializing database:")
        return 1
    finally:
        # Ensure all logs are flushed
        logging.shutdown()

if __name__ == "__main__":
    sys.exit(main())
