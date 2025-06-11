from PyQt6 import QtWidgets
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, 
                             QPushButton, QHBoxLayout, QLabel, QMessageBox, QHeaderView,
                             QDateEdit, QLineEdit, QGroupBox, QComboBox)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont, QColor, QAction
from datetime import datetime, date
from tenants_manager.utils.database import DatabaseManager
from tenants_manager.models.tenant import Payment, PaymentType, PaymentStatus, Tenant
from tenants_manager.views.payment_dialog import PaymentDialog

class PaymentHistoryWindow(QDialog):
    def __init__(self, tenant_id, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.tenant_id = tenant_id
        self.db = DatabaseManager()
        self.setWindowTitle("Histórico de Pagamentos")
        self.setMinimumSize(1000, 700)
        
        # Pagination
        self.current_page = 1
        self.items_per_page = 20
        self.total_payments = 0
        
        self.init_ui()
        self.load_tenant_data()
        self.load_payments_count()
        self.load_payments()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Balance information
        self.balance_label = QLabel()
        self.balance_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.balance_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        # Date range and search
        filter_layout = QHBoxLayout()
        
        # Date range
        date_group = QGroupBox("Período")
        date_layout = QHBoxLayout(date_group)
        
        date_layout.addWidget(QLabel("De:"))
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate().addMonths(-3))
        self.start_date.dateChanged.connect(self.on_date_changed)
        date_layout.addWidget(self.start_date)
        
        date_layout.addWidget(QLabel("Até:"))
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())
        self.end_date.dateChanged.connect(self.on_date_changed)
        date_layout.addWidget(self.end_date)
        
        filter_layout.addWidget(date_group)
        
        # Search
        search_group = QGroupBox("Pesquisar")
        search_layout = QHBoxLayout(search_group)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Pesquisar por descrição...")
        self.search_input.textChanged.connect(self.on_search_changed)
        search_layout.addWidget(self.search_input)
        
        filter_layout.addWidget(search_group)
        filter_layout.addStretch()
        
        # Update button
        update_btn = QPushButton("Atualizar")
        update_btn.clicked.connect(self.load_payments)
        filter_layout.addWidget(update_btn)
        
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
        
        # Pagination controls
        pagination_layout = QHBoxLayout()
        
        self.prev_btn = QPushButton("Anterior")
        self.prev_btn.clicked.connect(self.prev_page)
        pagination_layout.addWidget(self.prev_btn)
        
        self.page_label = QLabel("Página 1")
        pagination_layout.addWidget(self.page_label)
        
        self.next_btn = QPushButton("Próximo")
        self.next_btn.clicked.connect(self.next_page)
        pagination_layout.addWidget(self.next_btn)
        
        self.items_per_page_combo = QComboBox()
        self.items_per_page_combo.addItems(["10", "20", "50", "100"])
        self.items_per_page_combo.setCurrentText(str(self.items_per_page))
        self.items_per_page_combo.currentTextChanged.connect(self.on_items_per_page_changed)
        pagination_layout.addWidget(QLabel("Itens por página:"))
        pagination_layout.addWidget(self.items_per_page_combo)
        
        self.total_label = QLabel("Total: 0")
        pagination_layout.addWidget(self.total_label)
        
        # Layout
        layout.addLayout(filter_layout)
        layout.addWidget(self.balance_label)
        layout.addLayout(pagination_layout)
        layout.addWidget(self.payments_table)
        
        # Bottom buttons
        button_box = QHBoxLayout()
        close_btn = QPushButton("Fechar")
        close_btn.clicked.connect(self.accept)
        button_box.addStretch()
        button_box.addWidget(close_btn)
        
        layout.addLayout(button_box)
    
    def load_payments_count(self):
        """Load total count of payments for current filters"""
        with self.db.Session() as session:
            query = session.query(Payment).filter(
                Payment.tenant_id == self.tenant_id,
                Payment.payment_date >= self.start_date.date().toPyDate(),
                Payment.payment_date <= self.end_date.date().toPyDate()
            )
            
            search_text = self.search_input.text().strip().lower()
            if search_text:
                query = query.filter(Payment.description.ilike(f"%{search_text}%"))
                
            self.total_payments = query.count()
            self.total_label.setText(f"Total: {self.total_payments}")
            self.update_pagination_controls()
    
    def get_payments_query(self):
        """Get the base query with filters applied"""
        with self.db.Session() as session:
            query = session.query(Payment).filter(
                Payment.tenant_id == self.tenant_id,
                Payment.payment_date >= self.start_date.date().toPyDate(),
                Payment.payment_date <= self.end_date.date().toPyDate()
            )
            
            search_text = self.search_input.text().strip().lower()
            if search_text:
                query = query.filter(Payment.description.ilike(f"%{search_text}%"))
                
            return query.order_by(Payment.payment_date.desc())
    
    def load_payments(self):
        """Load payments for the selected page and filters"""
        # Clear existing rows
        self.payments_table.setRowCount(0)
        
        try:
            with self.db.Session() as session:
                # Get paginated results
                query = self.get_payments_query()
                
                # Apply pagination
                offset = (self.current_page - 1) * self.items_per_page
                payments = query.offset(offset).limit(self.items_per_page).all()
                
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
                
                # Update pagination controls
                self.update_pagination_controls()
                
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar pagamentos: {str(e)}")
    
    def update_pagination_controls(self):
        """Update the state of pagination controls"""
        total_pages = max(1, (self.total_payments + self.items_per_page - 1) // self.items_per_page)
        self.page_label.setText(f"Página {self.current_page} de {total_pages}")
        self.prev_btn.setEnabled(self.current_page > 1)
        self.next_btn.setEnabled(self.current_page < total_pages)
    
    def prev_page(self):
        """Go to the previous page"""
        if self.current_page > 1:
            self.current_page -= 1
            self.load_payments()
    
    def next_page(self):
        """Go to the next page"""
        self.current_page += 1
        self.load_payments()
    
    def on_items_per_page_changed(self, text):
        """Handle change in items per page"""
        self.items_per_page = int(text)
        self.current_page = 1  # Reset to first page
        self.load_payments_count()
        self.load_payments()
    
    def on_date_changed(self):
        """Handle date range change"""
        self.current_page = 1
        self.load_payments_count()
        self.load_payments()
    
    def on_search_changed(self, text):
        """Handle search text change"""
        self.current_page = 1
        self.load_payments_count()
        self.load_payments()
    
    def load_tenant_data(self):
        """Load tenant data and update the balance"""
        with self.db.Session() as session:
            tenant = session.get(Tenant, self.tenant_id)
            if tenant:
                self.setWindowTitle(f"Histórico de Pagamentos - {tenant.name}")
                self.update_balance()
    
    def update_balance(self):
        """Update the balance label"""
        with self.db.Session() as session:
            tenant = session.get(Tenant, self.tenant_id)
            if tenant:
                balance = tenant.get_balance()
                if balance > 0:
                    self.balance_label.setText(f"Saldo em dívida: <span style='color:red'>{balance:.2f} €</span>")
                else:
                    self.balance_label.setText(f"Crédito: <span style='color:green'>{-balance:.2f} €</span>")
            else:
                self.balance_label.setText("Inquilino não encontrado")
    
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
