"""Add is_confirmed to User model

Revision ID: f121b83e2cf3
Revises: b6e6590815ba
Create Date: 2025-06-20 17:17:07.936340

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f121b83e2cf3'
down_revision = 'b6e6590815ba'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('question', schema=None) as batch_op:
        batch_op.alter_column('options',
               existing_type=sa.TEXT(),
               type_=sa.JSON(),
               existing_nullable=False,
               postgresql_using='options::json')
        batch_op.alter_column('correct_answer',
               existing_type=sa.TEXT(),
               type_=sa.JSON(),
               existing_nullable=False,
               postgresql_using='correct_answer::json')

    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_confirmed', sa.Boolean(), server_default='0', nullable=False))
        batch_op.add_column(sa.Column('confirmed_on', sa.DateTime(), nullable=True))

    with op.batch_alter_table('user_answer', schema=None) as batch_op:
        batch_op.alter_column('user_selected_option',
               existing_type=sa.TEXT(),
               type_=sa.JSON(),
               existing_nullable=False,
               postgresql_using='user_selected_option::json')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user_answer', schema=None) as batch_op:
        batch_op.alter_column('user_selected_option',
               existing_type=sa.JSON(),
               type_=sa.TEXT(),
               existing_nullable=False)

    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('confirmed_on')
        batch_op.drop_column('is_confirmed')

    with op.batch_alter_table('question', schema=None) as batch_op:
        batch_op.alter_column('correct_answer',
               existing_type=sa.JSON(),
               type_=sa.TEXT(),
               existing_nullable=False)
        batch_op.alter_column('options',
               existing_type=sa.JSON(),
               type_=sa.TEXT(),
               existing_nullable=False)

    # ### end Alembic commands ###
