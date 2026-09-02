"""Add hostel_code, facilities, hostel_qr_code to hostels; add notices table

Revision ID: b3c2e7f9a012
Revises: a1d14d538a67
Create Date: 2026-07-05 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b3c2e7f9a012'
down_revision = 'a1d14d538a67'
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns to hostels table
    with op.batch_alter_table('hostels', schema=None) as batch_op:
        batch_op.add_column(sa.Column('hostel_code', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('facilities', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('hostel_qr_code', sa.String(length=200), nullable=True))
        batch_op.create_unique_constraint('uq_hostels_hostel_code', ['hostel_code'])

    # Create notices table
    op.create_table(
        'notices',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('hostel_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=150), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['hostel_id'], ['hostels.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('notices')

    with op.batch_alter_table('hostels', schema=None) as batch_op:
        batch_op.drop_constraint('uq_hostels_hostel_code', type_='unique')
        batch_op.drop_column('hostel_qr_code')
        batch_op.drop_column('facilities')
        batch_op.drop_column('hostel_code')
