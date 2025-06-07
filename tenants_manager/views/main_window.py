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
        
    def closeEvent(self, event):
        """Handle window close event"""
        try:
            # Close database session
            if self.session is not None:
                self.session.close()
            event.accept()
        except Exception as e:
            print(f"Error closing window: {str(e)}")
            event.accept()
    
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
        self.tenant_table.setColumnCount(8)  # Added room and rent columns
        self.tenant_table.setHorizontalHeaderLabels(["Nome", "Quarto", "Renda (€)", "BI", "Email", "Telefone", "Endereço", "Data de Nascimento"])
        
        # Enable single row selection
        self.tenant_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tenant_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.tenant_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)  # Make table read-only
        
        # Stretch columns to fill available space
        self.tenant_table.horizontalHeader().setStretchLastSection(True)
        
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
            tenant = dialog.get_tenant_data()
            if tenant:
                try:
                    # Get the session
                    session = self.db_manager.get_session()
                    
                    # Add the tenant to the session
                    session.add(tenant)
                    
                    # If there's an emergency contact, add it to the session
                    if hasattr(tenant, 'emergency_contact') and tenant.emergency_contact:
                        session.add(tenant.emergency_contact)
                    
                    # Commit the transaction
                    session.commit()
                    
                    # Refresh the tenant list
                    self.load_tenants()
                    QMessageBox.information(self, "Sucesso", "Inquilino adicionado com sucesso!")
                    
                except Exception as e:
                    session.rollback()
                    if 'UNIQUE constraint failed: tenants.bi' in str(e):
                        QMessageBox.critical(self, "Erro", "Este BI já está sendo usado por outro inquilino. Por favor, use um BI diferente.")
                    else:
                        QMessageBox.critical(self, "Erro", f"Erro ao adicionar inquilino: {str(e)}")
                finally:
                    session.close()
    
    def edit_tenant(self):
        # Get the selected row
        selected_rows = self.tenant_table.selectionModel().selectedRows()
        
        if not selected_rows:
            QMessageBox.warning(self, "Aviso", "Por favor, selecione um inquilino para editar.")
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
            dialog = TenantDialog(tenant=tenant, parent=self)
            
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
                    if hasattr(updated_tenant, 'emergency_contact') and updated_tenant.emergency_contact:
                        if hasattr(tenant, 'emergency_contact') and tenant.emergency_contact:
                            # Update existing emergency contact
                            ec = tenant.emergency_contact
                            updated_ec = updated_tenant.emergency_contact
                            ec.name = updated_ec.name
                            ec.phone = updated_ec.phone
                            ec.email = updated_ec.email
                        else:
                            # Add new emergency contact
                            tenant.emergency_contact = updated_tenant.emergency_contact
                    elif hasattr(tenant, 'emergency_contact') and tenant.emergency_contact:
                        # Remove existing emergency contact if it exists but was cleared
                        session.delete(tenant.emergency_contact)
                    
                    # Commit the changes
                    session.commit()
                    
                    # Refresh the table
                    self.load_tenants()
                    QMessageBox.information(self, "Sucesso", "Inquilino atualizado com sucesso!")
            
        except Exception as e:
            if session:
                session.rollback()
            QMessageBox.critical(self, "Erro", f"Erro ao atualizar inquilino: {str(e)}")
        finally:
            if session:
                session.close()
    
    def delete_tenant(self):
        # Get the selected row
        selected_rows = self.tenant_table.selectionModel().selectedRows()
        
        if not selected_rows:
            QMessageBox.warning(self, "Aviso", "Por favor, selecione um inquilino para excluir.")
            return
            
        # Get the selected row index
        row = selected_rows[0].row()
        
        # Get the tenant's BI (unique identifier) from the table
        bi = self.tenant_table.item(row, 3).text()
        
        # Ask for confirmation
        reply = QMessageBox.question(
            self, 
            'Confirmar Exclusão',
            f'Tem certeza que deseja excluir o inquilino {self.tenant_table.item(row, 0).text()}?\nBI: {bi}',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            session = None
            try:
                # Get the session
                session = self.db_manager.get_session()
                
                # Find the tenant by BI
                tenant = session.query(Tenant).filter_by(bi=bi).first()
                
                if not tenant:
                    QMessageBox.critical(self, "Erro", "Inquilino não encontrado!")
                    return
                
                # Delete the tenant (this will cascade to emergency_contact due to the relationship)
                session.delete(tenant)
                session.commit()
                
                # Refresh the table
                self.load_tenants()
                QMessageBox.information(self, "Sucesso", "Inquilino excluído com sucesso!")
                
            except Exception as e:
                if session:
                    session.rollback()
                QMessageBox.critical(self, "Erro", f"Erro ao excluir inquilino: {str(e)}")
            finally:
                if session:
                    session.close()
    
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
                self.tenant_table.setItem(row, 2, QTableWidgetItem(f"{tenant.rent:.2f}".replace('.', ',')))
                self.tenant_table.setItem(row, 3, QTableWidgetItem(tenant.bi))
                self.tenant_table.setItem(row, 4, QTableWidgetItem(tenant.email or ""))
                self.tenant_table.setItem(row, 5, QTableWidgetItem(tenant.phone or ""))
                self.tenant_table.setItem(row, 6, QTableWidgetItem(tenant.address or ""))
                self.tenant_table.setItem(row, 7, QTableWidgetItem(tenant.birth_date.strftime("%d/%m/%Y")))
                
            # Resize columns to fit content
            self.tenant_table.resizeColumnsToContents()
            
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar lista de inquilinos: {str(e)}")
