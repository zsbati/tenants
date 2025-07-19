"""Make room_id non-nullable and remove room string field

Revision ID: make_room_id_non_nullable
Revises: add_room_model
Create Date: 2025-07-19 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = 'make_room_id_non_nullable'
down_revision = 'add_room_model'
branch_labels = None
depends_on = None


def upgrade():
    # First, ensure all tenants have a room_id
    # This is a safety check - we should have handled this in the data migration
    # But we'll verify before making the column non-nullable
    conn = op.get_bind()
    result = conn.execute("SELECT COUNT(*) FROM tenants WHERE room_id IS NULL")
    null_room_count = result.scalar()
    
    if null_room_count > 0:
        raise Exception(f"Found {null_room_count} tenants without a room_id. "
                      f"Please ensure all tenants have a room_id before making it non-nullable.")
    
    # Make room_id non-nullable
    with op.batch_alter_table('tenants', schema=None) as batch_op:
        batch_op.alter_column('room_id', 
                            existing_type=sa.INTEGER(),
                            nullable=False)
    
    # Remove the old room string column
    with op.batch_alter_table('tenants', schema=None) as batch_op:
        batch_op.drop_column('room')


def downgrade():
    # Add back the room string column (nullable at first)
    with op.batch_alter_table('tenants', schema=None) as batch_op:
        batch_op.add_column(sa.Column('room', sa.String(length=50), nullable=True))
    
    # Copy room names back from rooms table
    conn = op.get_bind()
    conn.execute("""
        UPDATE tenants 
        SET room = (SELECT name FROM rooms WHERE rooms.id = tenants.room_id)
        WHERE room_id IS NOT NULL
    """)
    
    # Make room_id nullable again
    with op.batch_alter_table('tenants', schema=None) as batch_op:
        batch_op.alter_column('room_id', 
                            existing_type=sa.INTEGER(),
                            nullable=True)
