from PyQt6 import QtWidgets
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QHeaderView,
    QDateEdit,
    QLineEdit,
    QGroupBox,
    QComboBox,
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont, QColor, QAction
from datetime import datetime, date
from tenants_manager.utils.database import DatabaseManager
from tenants_manager.models.tenant import Payment, PaymentType, PaymentStatus, Tenant
from tenants_manager.views.payment_dialog import PaymentDialog


class PaymentHistoryWindow(QDialog):
    def __init__(self, tenant_id, parent_widget=None):
        super().__init__(parent_widget)
        self.parent_widget = parent_widget
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
        # Set default start date to 5 years ago or tenant's entry date, whichever is earlier
        five_years_ago = QDate.currentDate().addYears(-5)
        tenant_entry_date = self.get_tenant_entry_date()
        if tenant_entry_date and tenant_entry_date < five_years_ago.toPyDate():
            self.start_date.setDate(
                QDate(tenant_entry_date.year, tenant_entry_date.month, 1)
            )
        else:
            self.start_date.setDate(five_years_ago)
        self.start_date.dateChanged.connect(self.on_date_changed)
        date_layout.addWidget(self.start_date)

        date_layout.addWidget(QLabel("Até:"))
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        # Set default end date to end of current month
        today = QDate.currentDate()
        self.end_date.setDate(QDate(today.year(), today.month(), today.daysInMonth()))
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
        self.add_payment_btn.setStyleSheet(
            """
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
        """
        )

        # Payments table
        self.payments_table = QTableWidget()
        self.payments_table.setColumnCount(6)
        self.payments_table.setHorizontalHeaderLabels(
            ["Data", "Tipo", "Referência", "Valor", "Status", "Descrição"]
        )

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
        self.items_per_page_combo.currentTextChanged.connect(
            self.on_items_per_page_changed
        )
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
        search_text = self.search_input.text().strip()
        start_date = self.start_date.date().toPyDate()
        end_date = self.end_date.date().toPyDate()

        # This will update self.total_payments
        payments, self.total_payments = self.db.get_tenant_payments(
            tenant_id=self.tenant_id,
            start_date=start_date,
            end_date=end_date,
            page=1,  # Just get the first page for now
            per_page=self.items_per_page,
            search_term=search_text,
        )

        self.total_label.setText(f"Total: {self.total_payments}")
        self.update_pagination_controls()

    def get_payments_query(self):
        """Get payments with filters applied"""
        search_text = self.search_input.text().strip()
        start_date = self.start_date.date().toPyDate()
        end_date = self.end_date.date().toPyDate()

        payments, total = self.db.get_tenant_payments(
            tenant_id=self.tenant_id,
            start_date=start_date,
            end_date=end_date,
            page=self.current_page,
            per_page=self.items_per_page,
            search_term=search_text,
        )
        return payments

    def load_payments(self):
        """Load payments for the selected page and filters"""
        try:
            # Clear the table first and disable sorting to prevent issues
            self.payments_table.setSortingEnabled(False)
            self.payments_table.setRowCount(0)

            # Get the payments for the current page
            payments = self.get_payments_query()

            # Set row count in one go for better performance
            self.payments_table.setRowCount(len(payments))

            for row, payment in enumerate(payments):
                # Create items for each cell in the row

                # Date
                date_str = (
                    payment.payment_date.strftime("%d/%m/%Y")
                    if hasattr(payment, "payment_date") and payment.payment_date
                    else ""
                )
                date_item = QTableWidgetItem(date_str)

                # Type
                type_str = (
                    str(payment.payment_type.value)
                    if hasattr(payment, "payment_type") and payment.payment_type
                    else ""
                )
                type_item = QTableWidgetItem(type_str)

                # Reference month
                ref_month = ""
                if hasattr(payment, "reference_month") and payment.reference_month:
                    ref_month = payment.reference_month.strftime("%m/%Y")
                ref_item = QTableWidgetItem(ref_month)

                # Amount
                amount = getattr(payment, "amount", 0)
                amount_item = QTableWidgetItem(f"{amount:.2f} €")

                # Status
                status = getattr(payment, "status", "")
                if isinstance(status, str):
                    status_str = status
                elif hasattr(status, "value"):
                    status_str = status.value
                else:
                    status_str = str(status) if status is not None else ""
                status_item = QTableWidgetItem(status_str)

                # Description
                description = getattr(payment, "description", "")
                desc_item = QTableWidgetItem(description or "")

                # Add items to the table
                self.payments_table.setItem(row, 0, date_item)
                self.payments_table.setItem(row, 1, type_item)
                self.payments_table.setItem(row, 2, ref_item)
                self.payments_table.setItem(row, 3, amount_item)
                self.payments_table.setItem(row, 4, status_item)
                self.payments_table.setItem(row, 5, desc_item)

                # Store the payment ID in the row for reference
                if hasattr(payment, "id") and payment.id:
                    date_item.setData(Qt.ItemDataRole.UserRole, payment.id)

                # Color code the row based on payment status
                if hasattr(payment, "is_expected") and payment.is_expected:
                    color = QColor(230, 230, 230)  # Light gray for expected
                    # Make the text italic for expected payments
                    for col in range(self.payments_table.columnCount()):
                        item = self.payments_table.item(row, col)
                        if item:
                            font = item.font()
                            font.setItalic(True)
                            item.setFont(font)
                elif status == PaymentStatus.PENDING:
                    color = QColor(255, 255, 200)  # Light yellow for pending
                elif status == PaymentStatus.CANCELLED:
                    color = QColor(255, 200, 200)  # Light red for cancelled
                elif status == PaymentStatus.REFUNDED:
                    color = QColor(200, 255, 200)  # Light green for refunded
                else:
                    color = QColor(255, 255, 255)  # White for completed

                for col in range(self.payments_table.columnCount()):
                    item = self.payments_table.item(row, col)
                    if item:
                        item.setBackground(color)

            # Enable sorting after populating the table
            self.payments_table.setSortingEnabled(True)

            # Resize columns to fit content
            self.payments_table.resizeColumnsToContents()

            # Make the description column take remaining space
            header = self.payments_table.horizontalHeader()
            for i in range(header.count()):
                if i != 5:  # Don't stretch the description column
                    header.setSectionResizeMode(
                        i, QHeaderView.ResizeMode.ResizeToContents
                    )
            header.setSectionResizeMode(
                5, QHeaderView.ResizeMode.Stretch
            )  # Stretch description

            # Update pagination controls
            self.update_pagination_controls()

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar pagamentos: {str(e)}")

    def update_pagination_controls(self):
        """Update the state of pagination controls"""
        total_pages = max(
            1, (self.total_payments + self.items_per_page - 1) // self.items_per_page
        )
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

    def get_tenant_entry_date(self):
        """Get the tenant's entry date from the database"""
        with self.db.Session() as session:
            tenant = session.get(Tenant, self.tenant_id)
            if tenant and tenant.entry_date:
                if hasattr(tenant.entry_date, "date"):
                    return tenant.entry_date.date()
                return tenant.entry_date
            return None

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
                    self.balance_label.setText(
                        f"Saldo em dívida: <span style='color:red'>{balance:.2f} €</span>"
                    )
                else:
                    self.balance_label.setText(
                        f"Crédito: <span style='color:green'>{-balance:.2f} €</span>"
                    )
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
                    payment_data["tenant_id"] = self.tenant_id

                    # Record the payment
                    payment = self.db.record_payment(**payment_data)

                    if payment:
                        QMessageBox.information(
                            self,
                            "Sucesso",
                            f"Pagamento de {payment_data['amount']} € registado com sucesso!",
                        )
                        # Refresh the view
                        self.load_payments()
                        self.update_balance()
                        # Notify parent to refresh payments tab if needed
                        if self.parent_widget:
                            self.parent_widget.load_payments()
                    else:
                        QMessageBox.critical(
                            self, "Erro", "Falha ao registrar o pagamento!"
                        )

                except Exception as e:
                    QMessageBox.critical(
                        self,
                        "Erro",
                        f"Ocorreu um erro ao registrar o pagamento:\n{str(e)}",
                    )


class QDateEdit(QtWidgets.QDateEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCalendarPopup(True)
        self.setDisplayFormat("dd/MM/yyyy")
