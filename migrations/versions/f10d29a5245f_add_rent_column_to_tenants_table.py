"""Add rent column to tenants table

Revision ID: f10d29a5245f
Revises: 
Create Date: 2025-06-07 18:17:00.043934

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f10d29a5245f'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add the column as nullable first
    op.add_column('tenants', sa.Column('rent', sa.Float(), nullable=True))
    
    # Set a default value for existing rows
    op.execute("UPDATE tenants SET rent = 0.0 WHERE rent IS NULL")
    
    # Now alter the column to be NOT NULL
    with op.batch_alter_table('tenants') as batch_op:
        batch_op.alter_column('rent', existing_type=sa.Float(), nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('tenants', 'rent')
