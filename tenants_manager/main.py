import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTranslator
from tenants_manager.views.main_window import MainWindow

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    app = QApplication(sys.argv)
    
    # Set Portuguese locale
    translator = QTranslator()
    translator.load(f"i18n/pt.qm")
    app.installTranslator(translator)
    
    window = MainWindow()
    window.show()
    
    # Start the application
    app.exec()

if __name__ == "__main__":
    main()
