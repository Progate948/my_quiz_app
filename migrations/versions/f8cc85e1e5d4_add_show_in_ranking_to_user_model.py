"""Add show_in_ranking to User model

Revision ID: f8cc85e1e5d4
Revises: 567aca79260b
Create Date: 2025-06-25 12:16:14.897075

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f8cc85e1e5d4'
down_revision = '567aca79260b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('show_in_ranking', sa.Boolean(), nullable=False, server_default='1'))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('show_in_ranking')

    # ### end Alembic commands ###
