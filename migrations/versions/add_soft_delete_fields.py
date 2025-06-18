"""Add soft delete fields to Tenant model

Revision ID: add_soft_delete_fields
Revises: f10d29a5245f
Create Date: 2025-06-17 18:03:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = 'add_soft_delete_fields'
down_revision = 'f10d29a5245f'
branch_labels = None
depends_on = None

def upgrade():
    # Add is_active column with default True
    op.add_column('tenants', 
        sa.Column('is_active', sa.Boolean(), server_default='1', nullable=False)
    )
    
    # Add deleted_at column (nullable)
    op.add_column('tenants',
        sa.Column('deleted_at', sa.DateTime(), nullable=True)
    )
    
    # Create an index on is_active for better query performance
    op.create_index(op.f('ix_tenants_is_active'), 'tenants', ['is_active'], unique=False)

def downgrade():
    # Drop the index first
    op.drop_index(op.f('ix_tenants_is_active'), table_name='tenants')
    
    # Drop the columns
    op.drop_column('tenants', 'deleted_at')
    op.drop_column('tenants', 'is_active')
