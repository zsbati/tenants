from sqlalchemy import Column, Integer, String, Date, DateTime, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class EmergencyContact(Base):
    __tablename__ = 'emergency_contacts'

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id'))
    name = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)

    tenant = relationship("Tenant", back_populates="emergency_contact")

class Tenant(Base):
    __tablename__ = 'tenants'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    bi = Column(String(20), unique=True, nullable=False)  # Changed from CPF to BI
    email = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    address = Column(String(200), nullable=True)
    birth_date = Column(Date, nullable=False)
    entry_date = Column(Date, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship with contracts
    contracts = relationship("Contract", back_populates="tenant")
    
    # Relationship with emergency contact
    emergency_contact = relationship("EmergencyContact", back_populates="tenant", uselist=False)

class Contract(Base):
    __tablename__ = 'contracts'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id'))
    property_address = Column(String(200), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    monthly_rent = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship with tenant
    tenant = relationship("Tenant", back_populates="contracts")
