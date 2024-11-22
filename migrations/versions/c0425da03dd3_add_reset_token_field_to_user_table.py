"""Add reset_token field to User table

Revision ID: c0425da03dd3
Revises: 70de53917303
Create Date: 2024-11-22 16:23:30.461137

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c0425da03dd3'
down_revision = '70de53917303'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('reset_token', sa.String(length=36), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('reset_token')

    # ### end Alembic commands ###
