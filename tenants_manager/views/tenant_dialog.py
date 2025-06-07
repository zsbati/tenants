from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QFormLayout, QDateEdit, QMessageBox, QHBoxLayout, QGroupBox)
from PyQt6.QtCore import Qt, QDate
from tenants_manager.models.tenant import Tenant, EmergencyContact
from tenants_manager.utils.database import DatabaseManager

class TenantDialog(QDialog):
    def __init__(self, tenant=None, parent=None):
        super().__init__(parent)
        self.tenant = tenant
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Adicionar/Editar Inquilino")

        # Main layout
        layout = QVBoxLayout()
        
        # Name and Room
        name_room_layout = QHBoxLayout()
        
        # Name
        name_label = QLabel("Nome:")
        self.name_input = QLineEdit()
        name_layout = QHBoxLayout()
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_input)
        
        # Room
        room_label = QLabel("Quarto:")
        self.room_input = QLineEdit()
        room_layout = QHBoxLayout()
        room_layout.addWidget(room_label)
        room_layout.addWidget(self.room_input)
        
        name_room_layout.addLayout(name_layout)
        name_room_layout.addLayout(room_layout)

        # Form layout
        form_layout = QFormLayout()

        # BI (mandatory)
        self.bi_input = QLineEdit()
        self.bi_input.setPlaceholderText("Obrigatório")
        form_layout.addRow("BI:", self.bi_input)

        # Email (optional)
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Opcional")
        form_layout.addRow("Email:", self.email_input)

        # Phone (optional)
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("Opcional")
        form_layout.addRow("Telefone:", self.phone_input)
        
        # Rent (mandatory)
        self.rent_input = QLineEdit()
        self.rent_input.setPlaceholderText("Obrigatório")
        form_layout.addRow("Renda (€):", self.rent_input)

        # Address (optional)
        self.address_input = QLineEdit()
        self.address_input.setPlaceholderText("Opcional")
        form_layout.addRow("Endereço:", self.address_input)

        # Birth Date (mandatory)
        self.birth_input = QDateEdit()
        self.birth_input.setCalendarPopup(True)
        self.birth_input.setDate(QDate.currentDate())
        form_layout.addRow("Data de Nascimento:", self.birth_input)

        # Entry Date (mandatory)
        self.entry_input = QDateEdit()
        self.entry_input.setCalendarPopup(True)
        self.entry_input.setDate(QDate.currentDate())
        form_layout.addRow("Data de Entrada:", self.entry_input)

        # Emergency Contact (optional)
        emergency_group = QGroupBox("Contato de Emergência")
        emergency_layout = QFormLayout()

        self.emergency_name_input = QLineEdit()
        self.emergency_name_input.setPlaceholderText("Opcional")
        emergency_layout.addRow("Nome:", self.emergency_name_input)

        self.emergency_phone_input = QLineEdit()
        self.emergency_phone_input.setPlaceholderText("Opcional")
        emergency_layout.addRow("Telefone:", self.emergency_phone_input)

        self.emergency_email_input = QLineEdit()
        self.emergency_email_input.setPlaceholderText("Opcional")
        emergency_layout.addRow("Email:", self.emergency_email_input)

        emergency_group.setLayout(emergency_layout)
        layout.addWidget(emergency_group)

        # Add name and room layout to main layout
        layout.addLayout(name_room_layout)

        # Add form layout to main layout
        layout.addLayout(form_layout)

        # Add buttons
        button_box = QHBoxLayout()
        self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("Cancelar")
        button_box.addWidget(self.ok_button)
        button_box.addWidget(self.cancel_button)
        layout.addLayout(button_box)

        self.setLayout(layout)

        # Connect signals
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

        # If editing existing tenant, populate fields
        if self.tenant:
            self.name_input.setText(self.tenant.name)
            self.room_input.setText(self.tenant.room)
            self.rent_input.setText(str(self.tenant.rent))
            self.bi_input.setText(self.tenant.bi)
            self.email_input.setText(self.tenant.email)
            self.phone_input.setText(self.tenant.phone)
            self.address_input.setText(self.tenant.address)
            if self.tenant.birth_date:
                self.birth_input.setDate(self.tenant.birth_date)
            if self.tenant.entry_date:
                self.entry_input.setDate(self.tenant.entry_date)
            
            # Populate emergency contact if exists
            if self.tenant.emergency_contact:
                self.emergency_name_input.setText(self.tenant.emergency_contact.name)
                self.emergency_phone_input.setText(self.tenant.emergency_contact.phone)
                self.emergency_email_input.setText(self.tenant.emergency_contact.email)

    def get_tenant_data(self):
        # Validate mandatory fields
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Erro", "O nome é obrigatório!")
            return None
        if not self.room_input.text().strip():
            QMessageBox.warning(self, "Erro", "O quarto é obrigatório!")
            return None
        if not self.bi_input.text().strip():
            QMessageBox.warning(self, "Erro", "O BI é obrigatório!")
            return None
        if not self.birth_input.date().isValid():
            QMessageBox.warning(self, "Erro", "A data de nascimento é obrigatória!")
            return None
        if not self.entry_input.date().isValid():
            QMessageBox.warning(self, "Erro", "A data de entrada é obrigatória!")
            return None
            
        # Validate rent
        try:
            rent = float(self.rent_input.text().replace(',', '.'))
            if rent <= 0:
                QMessageBox.warning(self, "Erro", "A renda deve ser maior que zero!")
                return None
        except ValueError:
            QMessageBox.warning(self, "Erro", "Por favor, insira um valor numérico válido para a renda!")
            return None

        # Create tenant object
        tenant = Tenant()
        tenant.name = self.name_input.text()
        tenant.room = self.room_input.text()
        tenant.rent = float(self.rent_input.text().replace(',', '.'))
        tenant.bi = self.bi_input.text()
        tenant.email = self.email_input.text()
        tenant.phone = self.phone_input.text()
        tenant.address = self.address_input.text()
        tenant.birth_date = self.birth_input.date().toPyDate()
        tenant.entry_date = self.entry_input.date().toPyDate()

        # Create emergency contact if any fields are filled
        if any([self.emergency_name_input.text(), 
                self.emergency_phone_input.text(), 
                self.emergency_email_input.text()]):
            emergency_contact = EmergencyContact()
            emergency_contact.name = self.emergency_name_input.text()
            emergency_contact.phone = self.emergency_phone_input.text()
            emergency_contact.email = self.emergency_email_input.text()
            tenant.emergency_contact = emergency_contact

        return tenant
