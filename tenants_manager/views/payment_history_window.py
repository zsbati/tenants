from PyQt6 import QtWidgets
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, 
                             QPushButton, QHBoxLayout, QLabel, QMessageBox, QHeaderView,
                             QDateEdit, QLineEdit)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont, QColor
from datetime import datetime, date
from tenants_manager.utils.database import DatabaseManager
from tenants_manager.models.tenant import Payment, PaymentType, PaymentStatus, Tenant
from tenants_manager.views.payment_dialog import PaymentDialog

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
        self.add_payment_btn = QPushButton("Registrar Pagamento")
        self.add_payment_btn.clicked.connect(self.register_payment)
        date_layout.addWidget(self.add_payment_btn)
        
        # Set button style
        self.add_payment_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        
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
        """Load payments for the selected date range"""
        start_date = self.start_date.date().toPyDate()
        end_date = self.end_date.date().toPyDate()
        
        # Clear existing rows
        self.payments_table.setRowCount(0)
        
        # Get payments from database
        with self.db.Session() as session:
            # First, get all payments to show full history
            all_payments = session.query(Payment).filter(
                Payment.tenant_id == self.tenant_id
            ).order_by(Payment.payment_date.desc()).all()
            
            # Then filter by date range if needed
            payments = [
                p for p in all_payments 
                if start_date <= p.payment_date.date() <= end_date
            ]
            
            # If no payments in date range but there are payments, show all
            if not payments and all_payments:
                payments = all_payments
                # Update date range to show all payments
                if all_payments:
                    dates = [p.payment_date.date() for p in all_payments]
                    self.start_date.setDate(min(dates))
                    self.end_date.setDate(max(dates))
            
            for row, payment in enumerate(payments):
                self.payments_table.insertRow(row)
                
                # Date
                payment_date = payment.payment_date.date() if hasattr(payment.payment_date, 'date') else payment.payment_date
                date_item = QTableWidgetItem(payment_date.strftime("%d/%m/%Y"))
                date_item.setData(Qt.ItemDataRole.UserRole, payment.id)
                self.payments_table.setItem(row, 0, date_item)
                
                # Reference Month
                ref_date = payment.reference_month.date() if hasattr(payment.reference_month, 'date') else payment.reference_month
                ref_month = ref_date.strftime("%B %Y").capitalize()
                self.payments_table.setItem(row, 1, QTableWidgetItem(ref_month))
                
                # Amount
                self.payments_table.setItem(row, 2, QTableWidgetItem(f"{payment.amount:.2f} €"))
                
                # Type
                self.payments_table.setItem(row, 3, QTableWidgetItem(payment.payment_type.value.capitalize()))
                
                # Status
                status_item = QTableWidgetItem(payment.status.value.capitalize())
                
                # Set status color
                if payment.status == PaymentStatus.COMPLETED:
                    color = Qt.GlobalColor.darkGreen
                elif payment.status == PaymentStatus.PENDING:
                    color = Qt.GlobalColor.darkYellow
                else:
                    color = Qt.GlobalColor.darkRed
                    
                status_item.setForeground(color)
                self.payments_table.setItem(row, 4, status_item)
                
                # Description
                self.payments_table.setItem(row, 5, QTableWidgetItem(payment.description or ""))
                
                # Auto-resize columns to fit content
                self.payments_table.resizeColumnsToContents()
                
                # Make the table take full width
                header = self.payments_table.horizontalHeader()
                for i in range(header.count()):
                    if i != 5:  # Don't stretch the description column
                        header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
                header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)  # Stretch description
    
    def update_balance(self):
        """Update the balance label"""
        with self.db.Session() as session:
            tenant = session.query(Tenant).get(self.tenant_id)
            if tenant:
                balance = tenant.get_balance()
                color = "red" if balance > 0 else "green"
                self.balance_label.setText(f"Saldo: <span style='color:{color}'>{balance:.2f} €</span>")
                self.balance_label.setTextFormat(Qt.TextFormat.RichText)
    
    def register_payment(self):
        """Open dialog to register a new payment"""
        with self.db.Session() as session:
            tenant = session.query(Tenant).get(self.tenant_id)
            if not tenant:
                QMessageBox.warning(self, "Erro", "Inquilino não encontrado!")
                return
                
            payment_data = PaymentDialog.get_payment(tenant.name, self.db, self)
            if payment_data:
                try:
                    # Add tenant_id to payment data
                    payment_data['tenant_id'] = self.tenant_id
                    
                    # Record the payment
                    payment = self.db.record_payment(**payment_data)
                    
                    if payment:
                        QMessageBox.information(
                            self, 
                            "Sucesso", 
                            f"Pagamento de {payment_data['amount']} € registado com sucesso!"
                        )
                        # Refresh the view
                        self.load_payments()
                        self.update_balance()
                        # Notify parent to refresh payments tab if needed
                        if self.parent():
                            self.parent().load_payments()
                    else:
                        QMessageBox.critical(self, "Erro", "Falha ao registrar o pagamento!")
                        
                except Exception as e:
                    QMessageBox.critical(
                        self, 
                        "Erro", 
                        f"Ocorreu um erro ao registrar o pagamento:\n{str(e)}"
                    )


class QDateEdit(QtWidgets.QDateEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCalendarPopup(True)
        self.setDisplayFormat("dd/MM/yyyy")
