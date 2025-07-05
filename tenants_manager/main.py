import sys
import os
import logging
import logging.handlers
from datetime import datetime

# Import Qt modules at the top level
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt


def configure_logging():
    """Configure logging with appropriate levels and handlers.

    Log Levels:
    - DEBUG: Detailed information, typically of interest only when diagnosing problems.
    - INFO: Confirmation that things are working as expected.
    - WARNING: An indication that something unexpected happened.
    - ERROR: Due to a more serious problem, the software has not been able to perform some function.
    - CRITICAL: A serious error, indicating that the program itself may be unable to continue running.
    """
    # Determine log level from environment variable, default to INFO
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    try:
        log_level = getattr(logging, log_level)
    except AttributeError:
        log_level = logging.INFO

    # Create logs directory if it doesn't exist
    log_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs"
    )
    os.makedirs(log_dir, exist_ok=True)

    # Create a log file with current date (daily rotation)
    log_file = os.path.join(log_dir, f'app_{datetime.now().strftime("%Y%m%d")}.log')

    # Create formatter with fixed width for log levels
    formatter = logging.Formatter(
        "%(asctime)s - %(name)-30s - %(levelname)-8s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear any existing handlers to avoid duplicate logs
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Add file handler with rotation (20MB per file, keep 5 backups)
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=20 * 1024 * 1024, backupCount=5, encoding="utf-8"  # 20MB
    )
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Add console handler only if not in production
    if os.getenv("ENV") != "production":
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # Configure SQLAlchemy logging
    sql_logger = logging.getLogger("sqlalchemy")
    sql_logger.setLevel(logging.WARNING)  # Only show warnings and above
    sql_logger.propagate = False  # Prevent duplicate logs

    # Configure database module logging
    db_logger = logging.getLogger("tenants_manager.config.database")
    db_logger.setLevel(
        logging.WARNING if os.getenv("ENV") == "production" else logging.INFO
    )

    # Create and configure application logger
    app_logger = logging.getLogger("tenants_manager")
    app_logger.setLevel(log_level)

    # Add a filter to prevent duplicate logs
    class NoDuplicateFilter(logging.Filter):
        def filter(self, record):
            # Prevent duplicate log messages
            current_log = (
                record.module,
                record.levelno,
                record.msg % record.args if record.args else record.msg,
            )
            if not hasattr(self, "last_log"):
                self.last_log = None
            if current_log == self.last_log:
                return False
            self.last_log = current_log
            return True

    # Apply the filter to all handlers
    for handler in logging.root.handlers:
        handler.addFilter(NoDuplicateFilter())

    return app_logger


# Initialize logging
logger = configure_logging()


def main():
    """Main function to run the application."""
    logger.info("=" * 50)
    logger.info("STARTING APPLICATION")
    logger.info("=" * 50)

    # Log system information
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Python executable: {sys.executable}")
    logger.info(f"Working directory: {os.getcwd()}")
    logger.info(f"Script directory: {os.path.dirname(os.path.abspath(__file__))}")

    try:
        # Create the application
        logger.info("Creating QApplication...")
        app = QApplication.instance()
        if not app:
            app = QApplication(sys.argv)
            logger.info("New QApplication instance created")

            # Set application information
            app.setApplicationName("Tenants Manager")
            app.setApplicationVersion("1.0.0")
            app.setOrganizationName("Tenants Manager")
            logger.info("Application metadata set")

            # Translation support has been removed as requested
        else:
            logger.info("Using existing QApplication instance")

        # Create and show main window
        logger.info("Creating MainWindow...")
        window = MainWindow()
        logger.info("MainWindow created successfully")

        logger.info("Showing MainWindow...")
        window.show()
        logger.info("MainWindow shown")

        # Log window properties
        logger.info(f"MainWindow geometry: {window.geometry().getRect()}")
        logger.info(f"MainWindow is visible: {window.isVisible()}")
        logger.info(f"MainWindow window state: {window.windowState().name}")

        # Run application
        logger.info("Starting application event loop")
        exit_code = app.exec()
        logger.info(f"Application event loop ended with code: {exit_code}")
        return exit_code

    except Exception as e:
        logger.critical(f"FATAL ERROR: {str(e)}", exc_info=True)
        # Try to show error message box
        try:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setText("Critical Error")
            msg.setInformativeText(
                f"An error occurred: {str(e)}\n\nCheck the log file for details."
            )
            msg.setWindowTitle("Error")
            msg.exec()
        except Exception as ui_error:
            logger.critical(f"Could not show error dialog: {ui_error}")
        return 1


# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# Import MainWindow after setting up the path
try:
    from tenants_manager.views.main_window import MainWindow

    logger.info("Successfully imported MainWindow")
except ImportError as e:
    logger.error(f"Failed to import MainWindow: {e}")
    raise


def show_error_dialog(message, details=None):
    """Show an error dialog with optional details"""
    try:
        app = QApplication.instance() or QApplication(sys.argv)
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle("Application Error")
        msg.setText("An error occurred while starting the application.")
        msg.setInformativeText(str(message))

        if details:
            msg.setDetailedText(details)

        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        return msg.exec()
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Error showing error dialog: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
