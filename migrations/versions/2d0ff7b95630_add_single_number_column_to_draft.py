"""Add single_number column to Draft

Revision ID: 2d0ff7b95630
Revises: efec640f5d93
Create Date: 2023-12-07 11:58:09.182112

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2d0ff7b95630'
down_revision = 'efec640f5d93'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('draft', schema=None) as batch_op:
        batch_op.add_column(sa.Column('single_number', sa.Integer(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('draft', schema=None) as batch_op:
        batch_op.drop_column('single_number')

    # ### end Alembic commands ###
