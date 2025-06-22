import sys
from PyQt6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget

def main():
    app = QApplication(sys.argv)
    
    # Create main window
    window = QWidget()
    window.setWindowTitle("Test PyQt6")
    window.setGeometry(100, 100, 400, 200)
    
    # Add a label
    layout = QVBoxLayout()
    label = QLabel("If you can see this, PyQt6 is working!")
    layout.addWidget(label)
    window.setLayout(layout)
    
    # Show the window
    window.show()
    
    # Run the application
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
