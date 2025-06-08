from PyQt6 import QtWidgets
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, 
                             QPushButton, QHBoxLayout, QLabel, QMessageBox, QHeaderView,
                             QDateEdit)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont
from datetime import datetime, date
from tenants_manager.utils.database import DatabaseManager
from tenants_manager.models.tenant import PaymentType, PaymentStatus

class PaymentHistoryWindow(QDialog):
    def __init__(self, tenant_id, parent=None):
        super().__init__(parent)
        self.tenant_id = tenant_id
        self.db = DatabaseManager()
        self.setWindowTitle("Histórico de Pagamentos")
        self.setMinimumSize(800, 600)
        self.init_ui()
        self.load_payments()
        self.update_balance()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Balance information
        self.balance_label = QLabel()
        self.balance_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.balance_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        # Date range selection
        date_layout = QHBoxLayout()
        
        date_layout.addWidget(QLabel("De:"))
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate().addMonths(-6))  # Default to last 6 months
        date_layout.addWidget(self.start_date)
        
        date_layout.addWidget(QLabel("Até:"))
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())
        date_layout.addWidget(self.end_date)
        
        refresh_btn = QPushButton("Atualizar")
        refresh_btn.clicked.connect(self.load_payments)
        date_layout.addWidget(refresh_btn)
        
        date_layout.addStretch()
        
        # Add payment button
        add_payment_btn = QPushButton("Registrar Pagamento")
        add_payment_btn.clicked.connect(self.add_payment)
        date_layout.addWidget(add_payment_btn)
        
        # Payments table
        self.payments_table = QTableWidget()
        self.payments_table.setColumnCount(6)
        self.payments_table.setHorizontalHeaderLabels([
            "Data", "Tipo", "Referência", "Valor", "Status", "Descrição"
        ])
        
        # Configure table
        header = self.payments_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        
        # Layout
        layout.addWidget(self.balance_label)
        layout.addLayout(date_layout)
        layout.addWidget(self.payments_table)
        
        # Bottom buttons
        button_box = QHBoxLayout()
        close_btn = QPushButton("Fechar")
        close_btn.clicked.connect(self.accept)
        button_box.addStretch()
        button_box.addWidget(close_btn)
        
        layout.addLayout(button_box)
    
    def load_payments(self):
        self.payments_table.setRowCount(0)
        
        start_date = self.start_date.date().toPyDate()
        end_date = self.end_date.date().toPyDate()
        
        payments = self.db.get_tenant_payments(
            self.tenant_id, 
            start_date=start_date,
            end_date=end_date
        )
        
        for payment in payments:
            row = self.payments_table.rowCount()
            self.payments_table.insertRow(row)
            
            self.payments_table.setItem(row, 0, QTableWidgetItem(payment.payment_date.strftime("%d/%m/%Y %H:%M")))
            self.payments_table.setItem(row, 1, QTableWidgetItem(payment.payment_type.value.upper()))
            self.payments_table.setItem(row, 2, QTableWidgetItem(
                payment.reference_month.strftime("%m/%Y") if payment.reference_month else ""
            ))
            self.payments_table.setItem(row, 3, QTableWidgetItem(f"{payment.amount:.2f} €"))
            self.payments_table.setItem(row, 4, QTableWidgetItem(payment.status.value.upper()))
            self.payments_table.setItem(row, 5, QTableWidgetItem(payment.description or ""))
            
            # Color code the row based on payment status
            if payment.status == PaymentStatus.COMPLETED:
                color = "#e8f5e9"  # Light green
            elif payment.status == PaymentStatus.PENDING:
                color = "#fff8e1"  # Light yellow
            elif payment.status == PaymentStatus.CANCELLED:
                color = "#ffebee"  # Light red
            else:
                color = "#f5f5f5"  # Light gray
                
            for col in range(self.payments_table.columnCount()):
                item = self.payments_table.item(row, col)
                if item:
                    item.setBackground(color)
    
    def update_balance(self):
        balance = self.db.get_tenant_balance(self.tenant_id)
        if balance > 0:
            self.balance_label.setText(f"<span style='color: #d32f2f;'>Dívida: {balance:.2f} €</span>")
        elif balance < 0:
            self.balance_label.setText(f"<span style='color: #388e3c;'>Crédito: {abs(balance):.2f} €</span>")
        else:
            self.balance_label.setText("<span style='color: #388e3c;'>Conta em dia</span>")
    
    def add_payment(self):
        # This would open a dialog to add a new payment
        # For now, we'll just show a message
        QMessageBox.information(
            self,
            "Em Desenvolvimento",
            "Funcionalidade de registro de pagamento será implementada em breve."
        )
        # In a real implementation, you would open a dialog to enter payment details
        # and then call db.record_payment() with the entered values


class QDateEdit(QtWidgets.QDateEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCalendarPopup(True)
        self.setDisplayFormat("dd/MM/yyyy")
