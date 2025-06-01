from PyQt6.QtWidgets import (QMainWindow, QTabWidget, QPushButton, QVBoxLayout, QWidget, QTableWidget, QTableWidgetItem, QMessageBox, QHBoxLayout, QStatusBar, QTableView, QDialog)
from PyQt6.QtCore import Qt
from tenants_manager.views.tenant_dialog import TenantDialog
from tenants_manager.models.tenant import Tenant
from tenants_manager.utils.database import DatabaseManager
import sys
import os

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from tenants_manager.views.tenant_dialog import TenantDialog
from tenants_manager.models.tenant import Tenant
from tenants_manager.utils.database import DatabaseManager
import sys
import os

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestor de Inquilinos")
        self.setMinimumSize(1024, 768)
        self.db_manager = DatabaseManager()
        self.session = self.db_manager.get_session()
        self.init_ui()
        self.load_tenants()
    
    def init_ui(self):
        """Initialize the main window UI"""
        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Tab widget
        tabs = QTabWidget()
        tabs.addTab(self.create_tenants_tab(), "Inquilinos")
        tabs.addTab(self.create_contracts_tab(), "Contratos")
        
        layout.addWidget(tabs)
        
        # Status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)

    def create_tenants_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Button layout
        button_layout = QHBoxLayout()
        add_tenant_btn = QPushButton("Novo Inquilino")
        edit_tenant_btn = QPushButton("Editar Inquilino")
        delete_tenant_btn = QPushButton("Excluir Inquilino")
        
        button_layout.addWidget(add_tenant_btn)
        button_layout.addWidget(edit_tenant_btn)
        button_layout.addWidget(delete_tenant_btn)
        
        # Connect buttons
        add_tenant_btn.clicked.connect(self.add_tenant)
        edit_tenant_btn.clicked.connect(self.edit_tenant)
        delete_tenant_btn.clicked.connect(self.delete_tenant)
        
        layout.addLayout(button_layout)
        
        # Create tenant table
        self.tenant_table = QTableWidget()
        self.tenant_table.setColumnCount(7)  # Added room column
        self.tenant_table.setHorizontalHeaderLabels(["Nome", "Quarto", "BI", "Email", "Telefone", "Endereço", "Data de Nascimento"])
        
        layout.addWidget(self.tenant_table)
        
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
            tenant_data = dialog.get_tenant_data()
            if tenant_data:
                try:
                    # Create Tenant object from data
                    tenant = Tenant(
                        name=tenant_data['name'],
                        room=tenant_data['room'],
                        bi=tenant_data['bi'],
                        email=tenant_data['email'],
                        phone=tenant_data['phone'],
                        address=tenant_data['address'],
                        birth_date=tenant_data['birth_date'],
                        entry_date=tenant_data['entry_date']
                    )
                    
                    # Add emergency contact if provided
                    if tenant_data['emergency_contact']['name']:
                        tenant.emergency_contact = EmergencyContact(
                            name=tenant_data['emergency_contact']['name'],
                            phone=tenant_data['emergency_contact']['phone'],
                            email=tenant_data['emergency_contact']['email']
                        )
                    
                    # Add tenant to database
                    if self.db_manager.add_tenant(tenant):
                        self.load_tenants()
                        QMessageBox.information(self, "Sucesso", "Inquilino adicionado com sucesso!")
                    else:
                        QMessageBox.critical(self, "Erro", "Erro ao adicionar inquilino")
                except Exception as e:
                    if 'UNIQUE constraint failed: tenants.bi' in str(e):
                        QMessageBox.critical(self, "Erro", "Este BI já está sendo usado por outro inquilino. Por favor, use um BI diferente.")
                    else:
                        QMessageBox.critical(self, "Erro", f"Erro ao adicionar inquilino: {str(e)}")
    
    def edit_tenant(self):
        # TODO: Implement edit functionality
        QMessageBox.information(self, "Em Desenvolvimento", "Funcionalidade de edição em desenvolvimento")
    
    def delete_tenant(self):
        # TODO: Implement delete functionality
        QMessageBox.information(self, "Em Desenvolvimento", "Funcionalidade de exclusão em desenvolvimento")
    
    def load_tenants(self):
        """Load tenants from database and display them in the table"""
        try:
            tenants = self.db_manager.get_tenants()
            
            # Clear existing rows
            self.tenant_table.setRowCount(0)
            
            # Add rows for each tenant
            for tenant in tenants:
                row = self.tenant_table.rowCount()
                self.tenant_table.insertRow(row)
                
                # Add tenant data to each column
                self.tenant_table.setItem(row, 0, QTableWidgetItem(tenant.name))
                self.tenant_table.setItem(row, 1, QTableWidgetItem(tenant.room))
                self.tenant_table.setItem(row, 2, QTableWidgetItem(tenant.bi))
                self.tenant_table.setItem(row, 3, QTableWidgetItem(tenant.email or ""))
                self.tenant_table.setItem(row, 4, QTableWidgetItem(tenant.phone or ""))
                self.tenant_table.setItem(row, 5, QTableWidgetItem(tenant.address or ""))
                self.tenant_table.setItem(row, 6, QTableWidgetItem(tenant.birth_date.strftime("%d/%m/%Y")))
                
            # Resize columns to fit content
            self.tenant_table.resizeColumnsToContents()
            
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar lista de inquilinos: {str(e)}")
