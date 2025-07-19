from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFormLayout,
    QDateEdit,
    QMessageBox,
    QHBoxLayout,
    QGroupBox,
    QComboBox,
)
from sqlalchemy.orm import joinedload
from PyQt6.QtCore import Qt, QDate
from tenants_manager.models.tenant import Tenant, EmergencyContact
from tenants_manager.utils.database import DatabaseManager


class TenantDialog(QDialog):
    def __init__(self, tenant=None, parent=None, is_deleted=False):
        super().__init__(parent)
        self.tenant = tenant
        self.is_deleted = is_deleted
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Adicionar/Editar Inquilino")

        # Main layout
        layout = QVBoxLayout()

        # Show deletion status if viewing a deleted tenant
        if self.is_deleted:
            deleted_label = QLabel(
                "<span style='color: red; font-weight: bold;'>ESTE INQUILINO ESTÁ MARCADO COMO REMOVIDO</span>"
            )
            deleted_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(deleted_label)

            # Add a separator
            separator = QFrame()
            separator.setFrameShape(QFrame.Shape.HLine)
            separator.setFrameShadow(QFrame.Shadow.Sunken)
            layout.addWidget(separator)

        # Name and Room
        name_room_layout = QHBoxLayout()

        # Name
        name_label = QLabel("Nome:")
        self.name_input = QLineEdit()
        
        # Room selection
        room_label = QLabel("Quarto:")
        self.room_combo = QComboBox()
        self.room_combo.setEditable(True)  # Allow custom room names
        
        # Load existing rooms from database
        self.rooms = {}
        db_manager = DatabaseManager()
        with db_manager.get_session() as session:
            from tenants_manager.models.tenant import Room
            rooms = session.query(Room).order_by(Room.name).all()
            for room in rooms:
                self.room_combo.addItem(room.name, room.id)
                self.rooms[room.name.lower()] = room.id
        
        # Set up room name validation
        self.room_combo.lineEdit().setPlaceholderText("Digite o nome do quarto")
        self.room_combo.lineEdit().editingFinished.connect(self.validate_room_name)
        
        # Layout for name and room
        name_layout = QHBoxLayout()
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_input)
        
        room_layout = QHBoxLayout()
        room_layout.addWidget(room_label)
        room_layout.addWidget(self.room_combo)
        
        name_room_layout.addLayout(name_layout)
        name_room_layout.addLayout(room_layout)
        
        # If editing existing tenant, set the current room
        if self.tenant and self.tenant.room_ref:
            room_name = self.tenant.room_ref.name
            room_id = self.room_combo.findText(room_name)
            if room_id >= 0:
                self.room_combo.setCurrentIndex(room_id)
            else:
                # If room not found in the list, add it
                self.room_combo.addItem(room_name, self.tenant.room_id)
                self.room_combo.setCurrentText(room_name)

        # Form layout
        form_layout = QFormLayout()

        # BI (mandatory)
        self.bi_input = QLineEdit()
        self.bi_input.setPlaceholderText("Obrigatório")
        form_layout.addRow("BI:", self.bi_input)

        # Room input is now handled by the combo box above

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

        # Disable all inputs if viewing a deleted tenant
        if self.is_deleted:
            self.set_read_only(True)

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
            if self.tenant.room_ref:
                room_name = self.tenant.room_ref.name
                room_index = self.room_combo.findText(room_name)
                if room_index >= 0:
                    self.room_combo.setCurrentIndex(room_index)
                else:
                    # If room not in the list, add it
                    self.room_combo.addItem(room_name, self.tenant.room_ref.id)
                    self.room_combo.setCurrentText(room_name)
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

    def validate_room_name(self):
        """Validate room name format."""
        room_name = self.room_combo.currentText().strip()
        if not room_name:
            QMessageBox.warning(self, "Aviso", "O nome do quarto é obrigatório")
            return False
        if len(room_name) > 50:
            QMessageBox.warning(self, "Aviso", "O nome do quarto não pode ter mais de 50 caracteres")
            return False
        if not all(c.isalnum() or c.isspace() or c in '-_' for c in room_name):
            QMessageBox.warning(self, "Aviso", "O nome do quarto só pode conter letras, números, espaços, hífens e underscores")
            return False
            
        # If the room doesn't exist in our list, add it
        if room_name.lower() not in self.rooms:
            from tenants_manager.models.tenant import Room
            from sqlalchemy.exc import IntegrityError
            
            db_manager = DatabaseManager()
            with db_manager.get_session() as session:
                try:
                    room = Room(name=room_name, capacity=1)  # Default capacity of 1
                    session.add(room)
                    session.commit()
                    session.refresh(room)
                    
                    # Add to our local cache
                    self.rooms[room_name.lower()] = room.id
                    self.room_combo.addItem(room_name, room.id)
                    
                except IntegrityError:
                    # Room might have been added by another instance, refresh the list
                    session.rollback()
                    self.room_combo.clear()
                    rooms = session.query(Room).order_by(Room.name).all()
                    for r in rooms:
                        self.room_combo.addItem(r.name, r.id)
                        self.rooms[r.name.lower()] = r.id
                    
                    # Try to find the room again
                    room_id = self.room_combo.findText(room_name)
                    if room_id >= 0:
                        self.room_combo.setCurrentIndex(room_id)
                    else:
                        QMessageBox.warning(self, "Erro", "Não foi possível adicionar o quarto. Tente novamente.")
                        return False
                
        return True

    def get_tenant_data(self):
        """Get tenant data from form fields."""
        # Get room name from combo box
        room_name = self.room_combo.currentText().strip()
        room_id = self.room_combo.currentData()
        
        # If room_id is not set but we have a valid room name, use that
        if not room_id and room_name:
            room_id = self.rooms.get(room_name.lower())
        
        data = {
            "name": self.name_input.text().strip(),
            "room_id": room_id,
            "room_name": room_name,  # For creating a new room if needed
            "bi": self.bi_input.text().strip(),
            "email": self.email_input.text().strip() or None,
            "phone": self.phone_input.text().strip() or None,
            "rent": float(self.rent_input.text() or 0),
            "address": self.address_input.text().strip() or None,
            "birth_date": self.birth_input.date().toPyDate(),
            "entry_date": self.entry_input.date().toPyDate(),
            "emergency_contact": {
                "name": self.emergency_name_input.text().strip() or None,
                "phone": self.emergency_phone_input.text().strip() or None,
                "email": self.emergency_email_input.text().strip() or None,
            },
        }
        return data
