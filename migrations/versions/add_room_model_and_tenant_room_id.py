"""Add Room model and room_id to Tenant

Revision ID: add_room_model
Revises: 5cbc390f092c
Create Date: 2025-07-19 14:40:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = 'add_room_model'
down_revision = '5cbc390f092c'
branch_labels = None
depends_on = None


def upgrade():
    # Create rooms table
    op.create_table(
        'rooms',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False, comment="Room identifier (e.g., 'Quarto 101')"),
        sa.Column('capacity', sa.Integer(), nullable=False, server_default='4', comment='Maximum number of tenants allowed in the room (1-4)'),
        sa.Column('description', sa.String(length=200), nullable=True, comment='Optional description or notes about the room'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    
    # Add room_id column to tenants table (temporarily nullable for migration)
    with op.batch_alter_table('tenants', schema=None) as batch_op:
        batch_op.add_column(sa.Column('room_id', sa.Integer(), nullable=True))
    
    # Create foreign key constraint
    with op.batch_alter_table('tenants', schema=None) as batch_op:
        batch_op.create_foreign_key('fk_tenant_room', 'rooms', ['room_id'], ['id'])
    
    # Create index on room_id for better query performance
    op.create_index(op.f('ix_tenants_room_id'), 'tenants', ['room_id'], unique=False)


def downgrade():
    # Drop the index
    op.drop_index(op.f('ix_tenants_room_id'), table_name='tenants')
    
    # Drop the foreign key constraint
    with op.batch_alter_table('tenants', schema=None) as batch_op:
        batch_op.drop_constraint('fk_tenant_room', type_='foreignkey')
    
    # Drop the room_id column
    with op.batch_alter_table('tenants', schema=None) as batch_op:
        batch_op.drop_column('room_id')
    
    # Drop the rooms table
    op.drop_table('rooms')
