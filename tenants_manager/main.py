import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTranslator, QLocale
from tenants_manager.views.main_window import MainWindow
import signal

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
    
    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        print("\nApplication closed by user")
        sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main()
