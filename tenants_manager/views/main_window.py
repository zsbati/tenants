from PyQt6.QtWidgets import (
    QMainWindow,
    QTabWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QHBoxLayout,
    QStatusBar,
    QTableView,
    QDialog,
    QLabel,
    QMenu,
    QAbstractItemView,
    QHeaderView,
    QDateEdit,
    QFrame,
    QLineEdit,
    QCheckBox,
)
from PyQt6.QtCore import Qt, QDate, QLocale
from PyQt6.QtGui import QAction

import sys
import os
import logging

# Configure logger for this module
logger = logging.getLogger(__name__)

# Using system default locale for date formatting

# Add project root to Python path
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
if project_root not in sys.path:
    sys.path.append(project_root)

from tenants_manager.views.tenant_dialog import TenantDialog
from tenants_manager.views.payment_history_window import PaymentHistoryWindow
from tenants_manager.models.tenant import Tenant, PaymentType, PaymentStatus
from tenants_manager.utils.database import DatabaseManager


class MainWindow(QMainWindow):
    def __init__(self):
        try:
            super().__init__()
            logger.debug("Initializing MainWindow...")
            self.setWindowTitle("Gestor de Inquilinos")
            self.setMinimumSize(1024, 768)

            logger.debug("Creating DatabaseManager...")
            self.db_manager = DatabaseManager()
            logger.debug("Getting database session...")
            self.session = self.db_manager.get_session()

            # Pagination variables
            self.current_page = 1
            self.rows_per_page = 20
            self.total_tenants = 0
            self.search_term = ""

            logger.debug("Initializing UI...")
            self.init_ui()
            logger.debug("Loading tenants...")
            self.load_tenants()
            logger.info("Application started successfully")

        except Exception as e:
            logger.exception("Error during initialization")
            QMessageBox.critical(
                None,
                "Erro de Inicialização",
                f"Ocorreu um erro ao iniciar o aplicativo:\n\n{str(e)}\n\nVerifique o log para mais detalhes.",
            )
            raise  # Re-raise the exception to see the full traceback

    def closeEvent(self, event):
        """Handle window close event"""
        try:
            # Close database session
            if self.session is not None:
                self.session.close()
            event.accept()
        except Exception as e:
            logger.error(f"Error closing window: {str(e)}")
            event.accept()

    def init_ui(self):
        """Initialize the main window UI"""
        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_tenants_tab(), "Inquilinos")
        self.tabs.addTab(self.create_contracts_tab(), "Contratos")
        self.tabs.addTab(self.create_payments_tab(), "Pagamentos")

        layout.addWidget(self.tabs)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Add separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)

    def create_tenants_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Top button layout
        top_controls = QHBoxLayout()

        # Add Show Deleted checkbox
        self.show_deleted_checkbox = QCheckBox("Mostrar Inquilinos Removidos")
        self.show_deleted_checkbox.stateChanged.connect(self.toggle_deleted_tenants)
        top_controls.addWidget(self.show_deleted_checkbox)

        # Add spacer to push buttons to the right
        top_controls.addStretch()

        # Search bar
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Pesquisar inquilino...")
        self.search_input.returnPressed.connect(self.on_search)
        search_btn = QPushButton("Pesquisar")
        search_btn.clicked.connect(self.on_search)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(search_btn)

        # Action buttons
        button_layout = QHBoxLayout()
        add_tenant_btn = QPushButton("Novo Inquilino")
        edit_tenant_btn = QPushButton("Editar Inquilino")
        self.delete_tenant_btn = QPushButton("Excluir Inquilino")
        self.restore_tenant_btn = QPushButton("Restaurar Inquilino")

        button_layout.addWidget(add_tenant_btn)
        button_layout.addWidget(edit_tenant_btn)
        button_layout.addWidget(self.delete_tenant_btn)
        button_layout.addWidget(self.restore_tenant_btn)

        # Initially hide the restore button
        self.restore_tenant_btn.setVisible(False)

        # Add to top controls
        top_controls.addLayout(search_layout, 1)
        top_controls.addLayout(button_layout, 2)

        layout.addLayout(top_controls)

        # Connect buttons
        add_tenant_btn.clicked.connect(self.add_tenant)
        edit_tenant_btn.clicked.connect(self.edit_tenant)
        self.delete_tenant_btn.clicked.connect(self.delete_tenant)
        self.restore_tenant_btn.clicked.connect(self.restore_tenant)

        # Create tenant table
        self.tenant_table = QTableWidget()
        self.tenant_table.setColumnCount(9)  # Added one more column for status
        self.tenant_table.setHorizontalHeaderLabels(
            [
                "Nome",
                "Quarto",
                "Renda (€)",
                "BI",
                "Email",
                "Telefone",
                "Endereço",
                "Data de Nascimento",
                "Status",
            ]
        )

        # Update button states when selection changes
        self.tenant_table.itemSelectionChanged.connect(self.update_action_buttons)

        # Pagination controls
        pagination_layout = QHBoxLayout()

        self.prev_btn = QPushButton("Anterior")
        self.next_btn = QPushButton("Próximo")
        self.page_label = QLabel("Página 1")
        self.rows_label = QLabel("")

        self.prev_btn.clicked.connect(self.prev_page)
        self.next_btn.clicked.connect(self.next_page)

        pagination_layout.addWidget(self.prev_btn)
        pagination_layout.addWidget(self.page_label)
        pagination_layout.addWidget(self.next_btn)
        pagination_layout.addStretch()
        pagination_layout.addWidget(self.rows_label)

        layout.addLayout(pagination_layout)

        # Enable single row selection
        self.tenant_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.tenant_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.tenant_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )  # Make table read-only

        # Configure table
        header = self.tenant_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Name
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Room
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Rent
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # BI
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)  # Email
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Phone
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)  # Address
        header.setSectionResizeMode(
            7, QHeaderView.ResizeMode.ResizeToContents
        )  # Birth Date

        # Enable context menu
        self.tenant_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tenant_table.customContextMenuRequested.connect(
            self.show_tenant_context_menu
        )

        layout.addWidget(self.tenant_table)

        return widget

    def create_payments_tab(self):
        """Create the payments tab with overview of all tenants' payment status"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Button layout
        button_layout = QHBoxLayout()
        refresh_btn = QPushButton("Atualizar")
        refresh_btn.clicked.connect(self.load_payments)
        button_layout.addWidget(refresh_btn)

        # Add date range filter
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("Mês de Referência:"))
        self.reference_month = QDateEdit()
        self.reference_month.setCalendarPopup(True)
        self.reference_month.setDate(QDate.currentDate())
        self.reference_month.setDisplayFormat("MM/yyyy")
        self.reference_month.dateChanged.connect(self.load_payments)
        date_layout.addWidget(self.reference_month)

        button_layout.addStretch()
        button_layout.addLayout(date_layout)

        layout.addLayout(button_layout)

        # Add total rent collected and total debt labels
        totals_layout = QHBoxLayout()

        # Left side: Total rent collected
        rent_container = QWidget()
        rent_layout = QHBoxLayout(rent_container)
        rent_layout.setContentsMargins(0, 0, 0, 0)

        self.total_rent_label = QLabel("Total Arrecadado: 0.00 €")
        self.total_rent_label.setStyleSheet(
            "font-weight: bold; font-size: 14px; padding: 5px;"
        )
        rent_layout.addWidget(self.total_rent_label)
        totals_layout.addWidget(rent_container)

        # Add stretch to push the next label to the right
        totals_layout.addStretch()

        # Right side: Total debt
        debt_container = QWidget()
        debt_layout = QHBoxLayout(debt_container)
        debt_layout.setContentsMargins(0, 0, 0, 0)

        self.total_debt_label = QLabel("Dívida Total: 0.00 €")
        self.total_debt_label.setStyleSheet(
            "font-weight: bold; font-size: 14px; padding: 5px; "
            "color: red;"  # Red color for debt to make it stand out
        )
        debt_layout.addWidget(self.total_debt_label)
        totals_layout.addWidget(debt_container)

        layout.addLayout(totals_layout)

        # Create payments table
        self.payments_table = QTableWidget()
        self.payments_table.setColumnCount(6)
        self.payments_table.setHorizontalHeaderLabels(
            ["Inquilino", "Quarto", "Renda", "Status", "Valor Pago", "Saldo"]
        )

        # Configure table
        header = self.payments_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Name
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Room
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Rent
        header.setSectionResizeMode(
            3, QHeaderView.ResizeMode.ResizeToContents
        )  # Status
        header.setSectionResizeMode(
            4, QHeaderView.ResizeMode.ResizeToContents
        )  # Amount Paid
        header.setSectionResizeMode(
            5, QHeaderView.ResizeMode.ResizeToContents
        )  # Balance

        # Enable sorting
        self.payments_table.setSortingEnabled(True)

        # Enable selection
        self.payments_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.payments_table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )

        # Connect double click event
        self.payments_table.doubleClicked.connect(self.view_payment_history)

        layout.addWidget(self.payments_table)

        # Load initial data
        self.load_payments()

        return widget

    def create_contracts_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Button layout
        button_layout = QHBoxLayout()
        add_contract_btn = QPushButton("Novo Contrato")
        edit_contract_btn = QPushButton("Editar Contrato")
        delete_contract_btn = QPushButton("Excluir Contrato")

        button_layout.addWidget(add_contract_btn)
        button_layout.addWidget(edit_contract_btn)
        button_layout.addWidget(delete_contract_btn)

        layout.addLayout(button_layout)

        # Table view for contracts
        self.contract_table = QTableView()
        layout.addWidget(self.contract_table)

        return widget

    def add_tenant(self):
        dialog = TenantDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            tenant = dialog.get_tenant_data()
            if tenant:
                try:
                    # Get the session
                    session = self.db_manager.get_session()

                    # Add the tenant to the session
                    session.add(tenant)

                    # If there's an emergency contact, add it to the session
                    if (
                        hasattr(tenant, "emergency_contact")
                        and tenant.emergency_contact
                    ):
                        session.add(tenant.emergency_contact)

                    # Commit the transaction
                    session.commit()

                    # Refresh the tenant list
                    self.load_tenants()
                    self.load_payments()
                    QMessageBox.information(
                        self, "Sucesso", "Inquilino adicionado com sucesso!"
                    )

                except Exception as e:
                    session.rollback()
                    if "UNIQUE constraint failed: tenants.bi" in str(e):
                        QMessageBox.critical(
                            self,
                            "Erro",
                            "Este BI já está sendo usado por outro inquilino. Por favor, use um BI diferente.",
                        )
                    else:
                        QMessageBox.critical(
                            self, "Erro", f"Erro ao adicionar inquilino: {str(e)}"
                        )
                finally:
                    session.close()

    def edit_tenant(self):
        # Get the selected row
        selected_rows = self.tenant_table.selectionModel().selectedRows()

        if not selected_rows:
            QMessageBox.warning(
                self, "Aviso", "Por favor, selecione um inquilino para editar."
            )
            return

        # Get the selected row index
        row = selected_rows[0].row()

        # Get the tenant's BI (unique identifier) from the table
        bi = self.tenant_table.item(row, 3).text()

        session = None
        try:
            # Get the session
            session = self.db_manager.get_session()

            # Find the tenant by BI
            tenant = session.query(Tenant).filter_by(bi=bi).first()

            if not tenant:
                QMessageBox.critical(self, "Erro", "Inquilino não encontrado!")
                return

            # Create and show the edit dialog with the tenant's data
            dialog = TenantDialog(
                tenant=tenant, parent=self, is_deleted=not tenant.is_active
            )

            if dialog.exec() == QDialog.DialogCode.Accepted:
                # Get the updated tenant data
                updated_tenant = dialog.get_tenant_data()

                if updated_tenant:
                    # Update the tenant's properties
                    tenant.name = updated_tenant.name
                    tenant.room = updated_tenant.room
                    tenant.rent = updated_tenant.rent
                    tenant.bi = updated_tenant.bi
                    tenant.email = updated_tenant.email
                    tenant.phone = updated_tenant.phone
                    tenant.address = updated_tenant.address
                    tenant.birth_date = updated_tenant.birth_date
                    tenant.entry_date = updated_tenant.entry_date

                    # Handle emergency contact
                    if (
                        hasattr(updated_tenant, "emergency_contact")
                        and updated_tenant.emergency_contact
                    ):
                        if (
                            hasattr(tenant, "emergency_contact")
                            and tenant.emergency_contact
                        ):
                            # Update existing emergency contact
                            ec = tenant.emergency_contact
                            updated_ec = updated_tenant.emergency_contact
                            ec.name = updated_ec.name
                            ec.phone = updated_ec.phone
                            ec.email = updated_ec.email
                        else:
                            # Add new emergency contact
                            tenant.emergency_contact = updated_tenant.emergency_contact
                    elif (
                        hasattr(tenant, "emergency_contact")
                        and tenant.emergency_contact
                    ):
                        # Remove existing emergency contact if it exists but was cleared
                        session.delete(tenant.emergency_contact)

                    # Commit the changes
                    session.commit()

                    # Refresh the table
                    self.load_tenants()
                    self.load_payments()
                    QMessageBox.information(
                        self, "Sucesso", "Inquilino atualizado com sucesso!"
                    )

        except Exception as e:
            if session:
                session.rollback()
            QMessageBox.critical(self, "Erro", f"Erro ao atualizar inquilino: {str(e)}")
        finally:
            if session:
                session.close()

    def delete_tenant(self):
        """Soft delete the selected tenant"""
        current_row = self.tenant_table.currentRow()
        if current_row >= 0:
            tenant_id = self.tenant_table.item(current_row, 0).data(
                Qt.ItemDataRole.UserRole
            )

            reply = QMessageBox.question(
                self,
                "Confirmar",
                "Tem a certeza que deseja marcar este inquilino como removido?\n\n"
                + "O inquilino não será eliminado permanentemente e poderá ser restaurado posteriormente.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )

            if reply == QMessageBox.StandardButton.Yes:
                if self.db_manager.delete_tenant(tenant_id, hard_delete=False):
                    self.load_tenants()
                    QMessageBox.information(
                        self,
                        "Sucesso",
                        "Inquilino marcado como removido com sucesso!\n\n"
                        + 'Use a opção "Mostrar Inquilinos Removidos" para visualizá-lo.',
                    )
                else:
                    QMessageBox.warning(
                        self, "Erro", "Não foi possível remover o inquilino."
                    )

    def restore_tenant(self):
        """Restore a soft-deleted tenant"""
        current_row = self.tenant_table.currentRow()
        if current_row >= 0:
            tenant_id = self.tenant_table.item(current_row, 0).data(
                Qt.ItemDataRole.UserRole
            )

            reply = QMessageBox.question(
                self,
                "Confirmar",
                "Tem a certeza que deseja restaurar este inquilino?\n\n"
                + "O inquilino voltará a estar visível na lista principal.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )

            if reply == QMessageBox.StandardButton.Yes:
                if self.db_manager.restore_tenant(tenant_id):
                    self.load_tenants()
                    QMessageBox.information(
                        self,
                        "Sucesso",
                        "Inquilino restaurado com sucesso!\n\n"
                        + "O inquilino está agora visível na lista principal.",
                    )
                else:
                    QMessageBox.warning(
                        self, "Erro", "Não foi possível restaurar o inquilino."
                    )

    def toggle_deleted_tenants(self, state):
        """Toggle visibility of deleted tenants"""
        try:
            self.current_page = 1  # Reset to first page
            self.load_tenants()

            # Update the status bar message
            show_deleted = self.show_deleted_checkbox.isChecked()
            status_message = (
                "Mostrando todos os inquilinos (incluindo removidos)"
                if show_deleted
                else "Mostrando apenas inquilinos ativos"
            )
            self.status_bar.showMessage(status_message, 3000)  # Show for 3 seconds

        except Exception as e:
            logger.error(f"Error in toggle_deleted_tenants: {str(e)}")
            import traceback

            traceback.print_exc()
            QMessageBox.critical(
                self, "Erro", f"Erro ao alternar visualização de inquilinos: {str(e)}"
            )

    def load_tenants(self):
        """Load tenants from the database"""
        logger.debug("Starting load_tenants")
        try:
            logger.debug("1. Calculating pagination...")
            # Get the current page and rows per page
            offset = (self.current_page - 1) * self.rows_per_page
            show_deleted = self.show_deleted_checkbox.isChecked()
            logger.debug(
                f"   - Page: {self.current_page}, Offset: {offset}, Rows per page: {self.rows_per_page}"
            )
            logger.debug(f"   - Show deleted: {show_deleted}")

            logger.debug("2. Getting tenant count...")
            # Get total count of tenants (for pagination)
            try:
                total = self.db_manager.get_tenants_count(
                    search_term=self.search_term, include_deleted=show_deleted
                )
                logger.debug(f"   - Got tenant count: {total}")
            except Exception as e:
                logger.error(f"ERROR getting tenant count: {str(e)}")
                import traceback

                traceback.print_exc()
                total = 0

            self.total_tenants = total

            logger.debug("3. Fetching paginated tenants...")
            # Get paginated list of tenants
            try:
                tenants = self.db_manager.get_tenants_paginated(
                    offset=offset,
                    limit=self.rows_per_page,
                    search_term=self.search_term,
                    include_deleted=show_deleted,
                )
                logger.debug(f"   - Retrieved {len(tenants)} tenants")
            except Exception as e:
                logger.error(f"ERROR getting paginated tenants: {str(e)}")
                import traceback

                traceback.print_exc()
                tenants = []

            self.total_tenants = total
            total_pages = (
                (total + self.rows_per_page - 1) // self.rows_per_page
                if total > 0
                else 1
            )

            # Update pagination controls
            self.prev_btn.setEnabled(self.current_page > 1)
            self.next_btn.setEnabled(self.current_page < total_pages)
            self.page_label.setText(
                f"Página {self.current_page} de {max(1, total_pages)}"
            )

            start_item = (self.current_page - 1) * self.rows_per_page + 1
            end_item = min(start_item + len(tenants) - 1, total) if total > 0 else 0
            self.rows_label.setText(
                f"Mostrando {start_item}-{end_item} de {total} inquilinos"
            )

            # Clear existing rows
            self.tenant_table.setRowCount(0)

            # Debug: Print info about the tenants we received
            logger.debug(
                f"Loading {len(tenants)} tenants (page {self.current_page}, {self.rows_per_page} per page)"
            )

            # Add rows for each tenant
            for i, tenant in enumerate(tenants, 1):
                logger.debug(
                    f"Tenant {i}: Type={type(tenant)}, ID={getattr(tenant, 'id', 'N/A')}, Name={getattr(tenant, 'name', 'N/A')}"
                )

                if not hasattr(tenant, "id"):
                    logger.warning(f"Tenant object has no 'id' attribute: {tenant}")
                    continue

                row = self.tenant_table.rowCount()
                self.tenant_table.insertRow(row)

                try:
                    # Ensure we're passing a valid tenant ID
                    tenant_id = getattr(tenant, "id", None)
                    if tenant_id is None:
                        logger.warning(f"Tenant object has no 'id' attribute: {tenant}")
                        balance = 0.0
                    else:
                        logger.debug(f"Getting balance for tenant ID: {tenant_id}")
                        balance = self.db_manager.get_tenant_balance(tenant_id)
                except Exception as e:
                    logger.error(
                        f"Error getting balance for tenant {getattr(tenant, 'id', 'N/A')}: {str(e)}"
                    )
                    import traceback

                    traceback.print_exc()
                    balance = 0.0

                # Add tenant data to each column
                name_item = QTableWidgetItem(tenant.name)
                room_item = QTableWidgetItem(tenant.room)

                # Style deleted tenants with strikethrough and red color
                is_deleted = not getattr(tenant, "is_active", True)
                if is_deleted:
                    font = name_item.font()
                    font.setStrikeOut(True)
                    name_item.setFont(font)
                    room_item.setFont(font)
                    name_item.setForeground(Qt.GlobalColor.red)
                    room_item.setForeground(Qt.GlobalColor.red)

                self.tenant_table.setItem(row, 0, name_item)
                self.tenant_table.setItem(row, 1, room_item)

                # Format rent with balance information
                rent_item = QTableWidgetItem(f"{tenant.rent:.2f} €")
                if balance > 0:
                    rent_item.setForeground(Qt.GlobalColor.red)
                self.tenant_table.setItem(row, 2, rent_item)

                self.tenant_table.setItem(row, 3, QTableWidgetItem(tenant.bi))
                self.tenant_table.setItem(row, 4, QTableWidgetItem(tenant.email or ""))
                self.tenant_table.setItem(row, 5, QTableWidgetItem(tenant.phone or ""))
                self.tenant_table.setItem(
                    row, 6, QTableWidgetItem(tenant.address or "")
                )
                self.tenant_table.setItem(
                    row,
                    7,
                    QTableWidgetItem(
                        tenant.birth_date.strftime("%d/%m/%Y")
                        if tenant.birth_date
                        else ""
                    ),
                )

                # Add status as hidden data (is_deleted)
                status_item = QTableWidgetItem(
                    str(not getattr(tenant, "is_active", True))
                )
                self.tenant_table.setItem(row, 8, status_item)

                # Store the tenant ID in the first column for easy access
                self.tenant_table.item(row, 0).setData(
                    Qt.ItemDataRole.UserRole, tenant.id
                )

            # Resize columns to fit content
            self.tenant_table.resizeColumnsToContents()

            # Hide the status column
            self.tenant_table.setColumnHidden(8, True)

        except Exception as e:
            QMessageBox.critical(
                self, "Erro", f"Erro ao carregar lista de inquilinos: {str(e)}"
            )

    def on_search(self):
        """Handle search action"""
        self.current_page = 1
        self.search_term = self.search_input.text().strip()
        self.load_tenants()

    def prev_page(self):
        """Go to previous page"""
        if self.current_page > 1:
            self.current_page -= 1
            self.load_tenants()

    def next_page(self):
        """Go to next page"""
        total_pages = (
            self.total_tenants + self.rows_per_page - 1
        ) // self.rows_per_page
        if self.current_page < total_pages:
            self.current_page += 1
            self.load_tenants()

    def load_payments(self):
        """Load payment overview for all tenants"""
        self.payments_table.setRowCount(0)

        # Get the reference month
        ref_date = self.reference_month.date().toPyDate()

        # Update total rent collected
        total_rent = self.db_manager.get_total_rent_collected(ref_date) or 0.0

        # Format date in Portuguese
        month_year = ref_date.strftime("%B %Y").lower()
        # Capitalize the first letter of the month
        month_year = month_year[0].upper() + month_year[1:]

        # Update the total rent label with the formatted amount
        self.total_rent_label.setText(
            f"Total Arrecadado em {month_year}: {total_rent:.2f} €"
        )

        # Calculate and display total debt
        total_debt = self.db_manager.get_total_debt(ref_date) or 0.0
        self.total_debt_label.setText(f"Dívida Total: {total_debt:.2f} €")

        # Get all tenants - now returns (tenants, total_count)
        tenants, _ = self.db_manager.get_tenants()

        for tenant in tenants:
            if not hasattr(tenant, "id"):
                logger.warning(f"Invalid tenant object in load_payments: {tenant}")
                continue
            # Get payment status for the reference month
            payments, _ = self.db_manager.get_tenant_payments(
                tenant_id=tenant.id,
                reference_month=ref_date,
                page=1,  # Get all payments for the month
                per_page=1000,  # Arbitrarily large number to get all payments
            )

            # Calculate total paid for the reference month
            amount_paid = sum(
                p.amount for p in payments if p.status == PaymentStatus.COMPLETED
            )

            # Get current balance
            balance = self.db_manager.get_tenant_balance(tenant.id, as_of_date=ref_date)

            # Determine status
            if amount_paid >= tenant.rent:
                status = "Pago"
                status_color = Qt.GlobalColor.darkGreen
            elif amount_paid > 0:
                status = f"Parcial ({amount_paid/tenant.rent:.0%})"
                status_color = Qt.GlobalColor.darkYellow
            else:
                status = "Pendente"
                status_color = Qt.GlobalColor.red

            # Add row to table
            row = self.payments_table.rowCount()
            self.payments_table.insertRow(row)

            # Add data to table
            self.payments_table.setItem(row, 0, QTableWidgetItem(tenant.name))
            self.payments_table.setItem(row, 1, QTableWidgetItem(tenant.room))
            self.payments_table.setItem(
                row, 2, QTableWidgetItem(f"{tenant.rent:.2f} €")
            )

            status_item = QTableWidgetItem(status)
            status_item.setForeground(status_color)
            self.payments_table.setItem(row, 3, status_item)

            self.payments_table.setItem(
                row, 4, QTableWidgetItem(f"{amount_paid:.2f} €")
            )

            balance_item = QTableWidgetItem(f"{balance:.2f} €")
            if balance > 0:
                balance_item.setForeground(Qt.GlobalColor.red)
            elif balance < 0:
                balance_item.setForeground(Qt.GlobalColor.darkGreen)
            self.payments_table.setItem(row, 5, balance_item)

            # Store tenant ID in the row
            self.payments_table.item(row, 0).setData(
                Qt.ItemDataRole.UserRole, tenant.id
            )

    def view_payment_history(self):
        """View payment history for the selected tenant"""
        selected_rows = self.payments_table.selectionModel().selectedRows()
        if not selected_rows:
            return

        row = selected_rows[0].row()
        tenant_id = self.payments_table.item(row, 0).data(Qt.ItemDataRole.UserRole)

        dialog = PaymentHistoryWindow(tenant_id, parent_widget=self)
        dialog.exec()

    def update_action_buttons(self):
        """Update the visibility of action buttons based on the selected tenant's status"""
        try:
            if not hasattr(self, "tenant_table") or self.tenant_table.rowCount() == 0:
                self.delete_tenant_btn.setEnabled(False)
                self.restore_tenant_btn.setEnabled(False)
                return

            selected_rows = self.tenant_table.selectionModel().selectedRows()
            if not selected_rows:
                self.delete_tenant_btn.setEnabled(False)
                self.restore_tenant_btn.setEnabled(False)
                return

            row = selected_rows[0].row()

            # Make sure the row is valid
            if row < 0 or row >= self.tenant_table.rowCount():
                self.delete_tenant_btn.setEnabled(False)
                self.restore_tenant_btn.setEnabled(False)
                return

            # Get the status item safely
            status_item = self.tenant_table.item(row, 8)  # Status column
            if not status_item:
                # If status column is not available, assume tenant is active
                is_deleted = False
            else:
                is_deleted = status_item.text().lower() == "true"

            # Update button visibility and enabled state
            self.delete_tenant_btn.setEnabled(not is_deleted)
            self.restore_tenant_btn.setEnabled(is_deleted)
            self.delete_tenant_btn.setVisible(not is_deleted)
            self.restore_tenant_btn.setVisible(is_deleted)

        except Exception as e:
            logger.error(f"Error updating action buttons: {str(e)}")
            # Default to safe state
            self.delete_tenant_btn.setEnabled(False)
            self.restore_tenant_btn.setEnabled(False)

    def show_tenant_context_menu(self, position):
        """Show context menu for tenant row with appropriate actions"""
        try:
            if not hasattr(self, "tenant_table") or self.tenant_table.rowCount() == 0:
                return

            # Get the selected row
            selected_rows = self.tenant_table.selectionModel().selectedRows()
            if not selected_rows:
                return

            row = selected_rows[0].row()

            # Make sure the row is valid
            if row < 0 or row >= self.tenant_table.rowCount():
                return

            # Get the tenant ID and status
            tenant_id_item = self.tenant_table.item(
                row, 0
            )  # First column has tenant ID as UserRole
            status_item = self.tenant_table.item(row, 8)  # Status column

            if not tenant_id_item:
                return

            tenant_id = tenant_id_item.data(Qt.ItemDataRole.UserRole)

            # Get the status safely
            if not status_item:
                # If status column is not available, assume tenant is active
                is_deleted = False
            else:
                is_deleted = status_item.text().lower() == "true"

            # Create the context menu
            menu = QMenu()

            # Always show payment history option
            payment_action = menu.addAction("Ver Histórico de Pagamentos")
            menu.addSeparator()

            # Add edit action (only for active tenants)
            edit_action = None
            if not is_deleted:
                edit_action = menu.addAction("Editar Inquilino")

            # Add delete/restore action based on status
            if is_deleted:
                restore_action = menu.addAction("Restaurar Inquilino")
            else:
                delete_action = menu.addAction("Excluir Inquilino")

            # Show the menu and get the selected action
            action = menu.exec(self.tenant_table.viewport().mapToGlobal(position))

            # Handle the selected action
            if action == payment_action:
                # Show payment history for the selected tenant
                dialog = PaymentHistoryWindow(tenant_id, parent_widget=self)
                dialog.exec()
            elif not is_deleted and action == edit_action:
                self.edit_tenant()
            elif is_deleted and action == restore_action:
                self.restore_tenant()
            elif not is_deleted and action == delete_action:
                self.delete_tenant()

        except Exception as e:
            logger.error(f"Error showing context menu: {str(e)}")
            QMessageBox.critical(
                self, "Erro", f"Erro ao exibir menu de contexto: {str(e)}"
            )
