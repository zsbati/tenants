import logging
from sqlalchemy import (
    Boolean,
    Column,
    Integer,
    String,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Enum,
    func,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum as PyEnum

# Configure logger for this module
logger = logging.getLogger(__name__)

Base = declarative_base()


class EmergencyContact(Base):
    __tablename__ = "emergency_contacts"

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"))
    name = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)

    tenant = relationship("Tenant", back_populates="emergency_contact")


class PaymentStatus(PyEnum):
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentType(PyEnum):
    RENT = "rent"
    DEPOSIT = "deposit"
    FINE = "fine"
    OTHER = "other"


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    amount = Column(Float, nullable=False)
    payment_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    payment_type = Column(Enum(PaymentType), nullable=False, default=PaymentType.RENT)
    status = Column(
        Enum(PaymentStatus), nullable=False, default=PaymentStatus.COMPLETED
    )
    reference_month = Column(
        Date, nullable=False
    )  # First day of the month this payment is for
    description = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship with tenant
    tenant = relationship("Tenant", back_populates="payments")


class RentHistory(Base):
    __tablename__ = "rent_history"

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    amount = Column(Float, nullable=False)
    valid_from = Column(DateTime, default=datetime.utcnow, nullable=False)
    valid_to = Column(DateTime, nullable=True)  # NULL means current rent
    changed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    changed_by = Column(
        String(100), nullable=True
    )  # Could be linked to a user in the future

    # Relationship with tenant
    tenant = relationship("Tenant", back_populates="rent_history")


class Room(Base):
    __tablename__ = "rooms"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False, comment="Room identifier (e.g., 'Quarto 101')")
    capacity = Column(Integer, default=4, nullable=False, comment="Maximum number of tenants allowed in the room (1-4)")
    description = Column(String(200), nullable=True, comment="Optional description or notes about the room")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship with tenants (one-to-many)
    tenants = relationship("Tenant", back_populates="room_ref", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Room(id={self.id}, name='{self.name}', capacity={self.capacity})>"
    
    @property
    def current_occupancy(self):
        """Return the current number of active tenants in the room"""
        return len([t for t in self.tenants if t.is_active])
    
    @property
    def is_full(self):
        """Check if the room has reached its capacity"""
        return self.current_occupancy >= self.capacity


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False, comment="References the room this tenant is assigned to")
    rent = Column(Float, nullable=False)
    bi = Column(String(20), unique=True, nullable=False)
    email = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    address = Column(String(200), nullable=True)
    birth_date = Column(Date, nullable=False)
    entry_date = Column(Date, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True, nullable=False, server_default="1")
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    room_ref = relationship("Room", back_populates="tenants", foreign_keys=[room_id])
    contracts = relationship("Contract", back_populates="tenant")
    emergency_contact = relationship(
        "EmergencyContact", back_populates="tenant", uselist=False, cascade="all, delete-orphan"
    )
    payments = relationship(
        "Payment", back_populates="tenant", order_by="Payment.payment_date.desc()", cascade="all, delete-orphan"
    )
    rent_history = relationship(
        "RentHistory", back_populates="tenant", order_by="RentHistory.valid_from.desc()", cascade="all, delete-orphan"
    )

    def soft_delete(self):
        """Mark the tenant as deleted by setting is_active to False and deleted_at to current time"""
        self.is_active = False
        self.deleted_at = datetime.utcnow()

    def restore(self):
        """Restore a soft-deleted tenant by setting is_active to True and clearing deleted_at"""
        self.is_active = True
        self.deleted_at = None

    @classmethod
    def query_active(cls, session):
        """Return a query that filters out soft-deleted tenants"""
        return session.query(cls).filter_by(is_active=True)

    def update_rent(self, new_amount, changed_by=None, session=None):
        """Update the rent amount and create a historical record"""
        if session is None:
            from ..utils.database import DatabaseManager

            db = DatabaseManager()
            session = db.get_session()

        try:
            # Close the current rent history record if it exists
            current_rent = (
                session.query(RentHistory)
                .filter(
                    RentHistory.tenant_id == self.id, RentHistory.valid_to.is_(None)
                )
                .first()
            )

            if current_rent:
                current_rent.valid_to = datetime.utcnow()

            # Create new rent history record
            new_rent_history = RentHistory(
                tenant_id=self.id,
                amount=new_amount,
                valid_from=datetime.utcnow(),
                changed_by=changed_by,
            )

            # Update current rent
            self.rent = new_amount

            session.add(new_rent_history)
            session.commit()
            return True

        except Exception as e:
            session.rollback()
            logger.error(
                f"Error updating rent for tenant {self.id}: {str(e)}", exc_info=True
            )
            return False

    def get_balance(self, as_of_date=None):
        """Calculate the current balance (total rent due - total payments)"""
        if as_of_date is None:
            as_of_date = datetime.utcnow()

        # Convert as_of_date to date if it's a datetime
        if isinstance(as_of_date, datetime):
            as_of_date = as_of_date.date()

        # Get all rent periods up to as_of_date
        rent_periods = self._get_rent_periods(as_of_date)
        total_rent_due = sum(period["amount"] for period in rent_periods)

        # Get all payments up to as_of_date
        total_payments = sum(
            payment.amount
            for payment in self.payments
            if (
                payment.payment_date.date()
                if isinstance(payment.payment_date, datetime)
                else payment.payment_date
            )
            <= as_of_date
            and payment.status == PaymentStatus.COMPLETED
        )

        return total_rent_due - total_payments

    def _get_rent_periods(self, as_of_date=None):
        """Get all rent periods with their amounts up to the given date"""
        if as_of_date is None:
            as_of_date = datetime.utcnow()

        # Convert as_of_date to date if it's a datetime
        if isinstance(as_of_date, datetime):
            as_of_date = as_of_date.date()

        # Get all rent history records in chronological order
        history = sorted(self.rent_history, key=lambda x: x.valid_from)

        periods = []
        current_date = self.entry_date

        while current_date <= as_of_date:
            # Find the applicable rent for the current date
            applicable_rent = self.rent  # Default to current rent

            current_date_date = (
                current_date.date()
                if isinstance(current_date, datetime)
                else current_date
            )

            for record in history:
                valid_from = (
                    record.valid_from.date()
                    if isinstance(record.valid_from, datetime)
                    else record.valid_from
                )
                valid_to = (
                    record.valid_to.date()
                    if record.valid_to and isinstance(record.valid_to, datetime)
                    else record.valid_to
                )

                if valid_from <= current_date_date and (
                    valid_to is None or valid_to >= current_date_date
                ):
                    applicable_rent = record.amount
                    break

            # Add to periods
            periods.append({"date": current_date_date, "amount": applicable_rent})

            # Move to next month
            if current_date.month == 12:
                current_date = current_date.replace(
                    year=current_date.year + 1, month=1, day=1
                )
            else:
                current_date = current_date.replace(month=current_date.month + 1, day=1)

            # Ensure current_date is a date object for the next iteration
            if isinstance(current_date, datetime):
                current_date = current_date.date()

        return periods


class Contract(Base):
    __tablename__ = "contracts"

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"))
    property_address = Column(String(200), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    monthly_rent = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship with tenant
    tenant = relationship("Tenant", back_populates="contracts")
