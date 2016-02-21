"""logpage

Revision ID: 27315cdf3f84
Revises: 8c6a92703ad
Create Date: 2016-02-20 16:24:55.870325

"""

# revision identifiers, used by Alembic.
revision = '27315cdf3f84'
down_revision = '8c6a92703ad'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('log_pages',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('chat_id', sa.Integer(), nullable=False),
    sa.Column('page', sa.Integer(), nullable=False),
    sa.Column('offset', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['chat_id'], ['chats.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.drop_column(u'invites', 'unread')
    op.drop_index('messages_posted_idx', table_name='messages')
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_index('messages_posted_idx', 'messages', ['posted'], unique=False)
    op.add_column(u'invites', sa.Column('unread', sa.BOOLEAN(), server_default=sa.text(u'true'), autoincrement=False, nullable=False))
    op.drop_table('log_pages')
    ### end Alembic commands ###
