"""Merge master and epicurean branches

Revision ID: 2075274e8da8
Revises: 30a41ccc3c3c, 2bba6143a470
Create Date: 2016-03-14 19:08:40.827276

"""

# revision identifiers, used by Alembic.
revision = '2075274e8da8'
down_revision = ('30a41ccc3c3c', '2bba6143a470')
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    pass


def downgrade():
    pass
