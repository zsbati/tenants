from PyQt6.QtWidgets import (QMainWindow, QTabWidget, QPushButton, QVBoxLayout, QWidget, QTableWidget, QTableWidgetItem, QMessageBox, QHBoxLayout, QStatusBar, QTableView)
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
        
        # Table view for tenants
        self.tenant_table = QTableView()
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
                    if self.db_manager.add_tenant(tenant_data):
                        self.load_tenants()
                        QMessageBox.information(self, "Sucesso", "Inquilino adicionado com sucesso!")
                    else:
                        QMessageBox.critical(self, "Erro", "Erro ao adicionar inquilino")
                except Exception as e:
                    QMessageBox.critical(self, "Erro", f"Erro ao adicionar inquilino: {str(e)}")
    
    def edit_tenant(self):
        # TODO: Implement edit functionality
        QMessageBox.information(self, "Em Desenvolvimento", "Funcionalidade de edição em desenvolvimento")
    
    def delete_tenant(self):
        # TODO: Implement delete functionality
        QMessageBox.information(self, "Em Desenvolvimento", "Funcionalidade de exclusão em desenvolvimento")
    
    def load_tenants(self):
        # TODO: Implement table model loading
        pass
