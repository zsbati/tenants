from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QComboBox, QDateEdit, QDoubleSpinBox, 
                             QMessageBox, QFormLayout, QLineEdit)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont
from datetime import datetime
from tenants_manager.models.tenant import PaymentType, PaymentStatus

class PaymentDialog(QDialog):
    def __init__(self, tenant_name, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.setWindowTitle(f"Registrar Pagamento - {tenant_name}")
        self.setMinimumWidth(400)
        
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Form layout for input fields
        form_layout = QFormLayout()
        
        # Amount
        self.amount_input = QDoubleSpinBox()
        self.amount_input.setMinimum(0.01)
        self.amount_input.setMaximum(1000000)
        self.amount_input.setDecimals(2)
        self.amount_input.setPrefix("€ ")
        
        # Payment type
        self.type_combo = QComboBox()
        # Add translated payment types
        for payment_type in PaymentType:
            self.type_combo.addItem(self.tr(payment_type.value), payment_type)
        
        # Payment date (default to today)
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setDisplayFormat("dd/MM/yyyy")
        
        # Reference month (default to current month)
        self.reference_month_edit = QDateEdit()
        self.reference_month_edit.setCalendarPopup(True)
        self.reference_month_edit.setDate(QDate.currentDate())
        self.reference_month_edit.setDisplayFormat("MM/yyyy")
        
        # Description
        self.description_edit = QLineEdit()
        self.description_edit.setPlaceholderText("Ex: Pagamento de renda, depósito, etc.")
        
        # Add fields to form
        form_layout.addRow("Valor:", self.amount_input)
        form_layout.addRow("Tipo de pagamento:", self.type_combo)
        form_layout.addRow("Data do pagamento:", self.date_edit)
        form_layout.addRow("Mês de referência:", self.reference_month_edit)
        form_layout.addRow("Descrição:", self.description_edit)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton("Salvar")
        self.save_button.clicked.connect(self.accept)
        
        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        
        # Add to main layout
        layout.addLayout(form_layout)
        layout.addLayout(button_layout)
    
    def get_payment_data(self):
        """Return the payment data as a dictionary"""
        return {
            'amount': self.amount_input.value(),
            'payment_type': self.type_combo.currentData(),
            'payment_date': self.date_edit.date().toPyDate(),
            'reference_month': self.reference_month_edit.date().toPyDate(),
            'description': self.description_edit.text().strip() or None,
            'status': PaymentStatus.COMPLETED
        }
    
    @staticmethod
    def get_payment(tenant_name, db_manager, parent=None):
        """Static method to create the dialog and return the payment data"""
        dialog = PaymentDialog(tenant_name, db_manager, parent)
        result = dialog.exec()
        
        if result == QDialog.DialogCode.Accepted:
            return dialog.get_payment_data()
        return None
