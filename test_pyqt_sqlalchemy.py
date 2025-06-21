import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QLabel, QPushButton, QTextEdit, QMessageBox)
from PyQt6.QtCore import Qt
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Set up SQLAlchemy
Base = declarative_base()

class TestModel(Base):
    __tablename__ = 'test_table'
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt6 + SQLAlchemy Test")
        self.setGeometry(100, 100, 600, 400)
        
        # Database setup
        self.db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                  'tenants_manager', 'tenants.db')
        self.engine = None
        self.Session = None
        
        # Setup UI
        self.setup_ui()
        
        # Test database connection
        self.test_database()
    
    def setup_ui(self):
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout
        layout = QVBoxLayout(central_widget)
        
        # Status label
        self.status_label = QLabel("Status: Not connected")
        layout.addWidget(self.status_label)
        
        # Database path
        path_label = QLabel(f"Database: {self.db_path}")
        path_label.setWordWrap(True)
        layout.addWidget(path_label)
        
        # Test buttons
        btn_test = QPushButton("Test Connection")
        btn_test.clicked.connect(self.test_database)
        layout.addWidget(btn_test)
        
        btn_create = QPushButton("Create Test Table")
        btn_create.clicked.connect(self.create_test_table)
        layout.addWidget(btn_create)
        
        btn_query = QPushButton("Query Test Table")
        btn_query.clicked.connect(self.query_test_table)
        layout.addWidget(btn_query)
        
        # Log area
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        layout.addWidget(self.log_area)
        
        # Quit button
        btn_quit = QPushButton("Quit")
        btn_quit.clicked.connect(self.close)
        layout.addWidget(btn_quit)
    
    def log(self, message):
        """Add a message to the log area"""
        self.log_area.append(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
        QApplication.processEvents()
    
    def test_database(self):
        """Test database connection"""
        try:
            self.log("Testing database connection...")
            db_url = f"sqlite:///{self.db_path}"
            self.log(f"Connecting to: {db_url}")
            
            self.engine = create_engine(db_url, echo=True)
            self.Session = sessionmaker(bind=self.engine)
            
            # Test connection
            with self.engine.connect() as conn:
                result = conn.execute("SELECT sqlite_version()")
                version = result.scalar()
                
            self.status_label.setText(f"Status: Connected (SQLite {version})")
            self.status_label.setStyleSheet("color: green;")
            self.log("✓ Database connection successful")
            return True
            
        except Exception as e:
            error_msg = f"Database connection failed: {str(e)}"
            self.status_label.setText("Status: Connection failed")
            self.status_label.setStyleSheet("color: red;")
            self.log(f"✗ {error_msg}")
            QMessageBox.critical(self, "Database Error", error_msg)
            return False
    
    def create_test_table(self):
        """Create a test table"""
        if not self.engine:
            QMessageBox.warning(self, "Error", "Not connected to database")
            return
            
        try:
            self.log("Creating test table...")
            Base.metadata.create_all(self.engine)
            self.log("✓ Test table created successfully")
        except Exception as e:
            error_msg = f"Failed to create test table: {str(e)}"
            self.log(f"✗ {error_msg}")
            QMessageBox.critical(self, "Error", error_msg)
    
    def query_test_table(self):
        """Query the test table"""
        if not self.Session:
            QMessageBox.warning(self, "Error", "Not connected to database")
            return
            
        try:
            self.log("Querying test table...")
            session = self.Session()
            
            # Add a test record
            test_record = TestModel(name=f"Test at {datetime.now()}")
            session.add(test_record)
            session.commit()
            
            # Query all records
            records = session.query(TestModel).order_by(TestModel.created_at.desc()).all()
            
            if not records:
                self.log("No records found in test table")
            else:
                self.log(f"Found {len(records)} records:")
                for i, record in enumerate(records, 1):
                    self.log(f"  {i}. ID: {record.id}, Name: {record.name}, Created: {record.created_at}")
            
            session.close()
            
        except Exception as e:
            error_msg = f"Query failed: {str(e)}"
            self.log(f"✗ {error_msg}")
            QMessageBox.critical(self, "Error", error_msg)

def main():
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show the main window
    window = TestWindow()
    window.show()
    
    # Run the application
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
