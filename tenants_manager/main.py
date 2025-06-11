import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTranslator

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tenants_manager.views.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    
    # Set Portuguese locale
    translator = QTranslator()
    if translator.load("pt", "i18n", ".qm"):
        app.installTranslator(translator)
    
    try:
        window = MainWindow()
        window.show()
        return app.exec()
    except Exception as e:
        print(f"Error starting application: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
