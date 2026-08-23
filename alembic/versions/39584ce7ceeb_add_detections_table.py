"""add detections table

Revision ID: 39584ce7ceeb
Revises: ecc21315ecf6
Create Date: 2026-08-19 18:55:26.024784

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '39584ce7ceeb'
down_revision: Union[str, Sequence[str], None] = 'ecc21315ecf6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('detections',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('product_id', sa.Integer(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('criteria', sa.String(), nullable=False),
    sa.Column('price', sa.Integer(), nullable=False),
    sa.Column('detected_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('sent_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_detections_id'), 'detections', ['id'], unique=False)
    op.create_index('ix_detections_sent_at', 'detections', ['sent_at'], unique=False)
    op.drop_index(op.f('ix_scraper_erros_product_captured'), table_name='scraper_errors')
    op.create_index('ix_scraper_errors_product_captured', 'scraper_errors', ['product_id', 'captured_at'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_scraper_errors_product_captured', table_name='scraper_errors')
    op.create_index(op.f('ix_scraper_erros_product_captured'), 'scraper_errors', ['product_id', 'captured_at'], unique=False)
    op.drop_index('ix_detections_sent_at', table_name='detections')
    op.drop_index(op.f('ix_detections_id'), table_name='detections')
    op.drop_table('detections')
