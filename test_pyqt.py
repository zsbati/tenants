import sys
from PyQt6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget, QPushButton

def on_button_click():
    print("Button clicked!")

def main():
    print("Starting PyQt6 test...")
    
    try:
        # Create the application
        app = QApplication(sys.argv)
        print("QApplication created successfully")
        
        # Create the main window
        window = QWidget()
        window.setWindowTitle("PyQt6 Test")
        window.setGeometry(100, 100, 400, 200)
        
        # Create a layout
        layout = QVBoxLayout()
        
        # Add a label
        label = QLabel("PyQt6 is working!")
        layout.addWidget(label)
        
        # Add a button
        button = QPushButton("Click me!")
        button.clicked.connect(on_button_click)
        layout.addWidget(button)
        
        # Set the layout
        window.setLayout(layout)
        
        # Show the window
        window.show()
        print("Window shown")
        
        # Run the application
        print("Starting event loop...")
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
