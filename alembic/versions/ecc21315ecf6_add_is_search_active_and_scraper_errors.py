"""add is_search_active and scraper_errors

Revision ID: ecc21315ecf6
Revises: 7044525d7eea
Create Date: 2026-08-12 14:21:09.130502

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ecc21315ecf6'
down_revision: Union[str, Sequence[str], None] = '7044525d7eea'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

naming_convention = {"fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s"}


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('scraper_errors',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=True),
        sa.Column('error_type', sa.String(), nullable=False),
        sa.Column('message', sa.String(), nullable=True),
        sa.Column('captured_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('is_fix', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_scraper_errors_id'), 'scraper_errors', ['id'], unique=False)
    op.create_index('ix_scraper_erros_product_captured', 'scraper_errors', ['product_id', 'captured_at'], unique=False)

    with op.batch_alter_table('products', naming_convention=naming_convention) as batch_op:
        batch_op.add_column(sa.Column('is_search_active', sa.Boolean(), nullable=True, server_default=sa.text('1')))
        batch_op.alter_column('title', existing_type=sa.VARCHAR(), nullable=False)
        batch_op.alter_column('link', existing_type=sa.VARCHAR(), nullable=False)
        batch_op.drop_constraint('fk_products_owner_id_users', type_='foreignkey')
        batch_op.create_foreign_key('fk_products_owner_id_users', 'users', ['owner_id'], ['id'], ondelete='SET NULL')

    with op.batch_alter_table('users') as batch_op:
        batch_op.alter_column('email', existing_type=sa.VARCHAR(), nullable=False)
        batch_op.alter_column('username', existing_type=sa.VARCHAR(), nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('users') as batch_op:
        batch_op.alter_column('username', existing_type=sa.VARCHAR(), nullable=True)
        batch_op.alter_column('email', existing_type=sa.VARCHAR(), nullable=True)

    with op.batch_alter_table('products', naming_convention=naming_convention) as batch_op:
        batch_op.drop_constraint('fk_products_owner_id_users', type_='foreignkey')
        batch_op.create_foreign_key('fk_products_owner_id_users', 'users', ['owner_id'], ['id'])
        batch_op.alter_column('link', existing_type=sa.VARCHAR(), nullable=True)
        batch_op.alter_column('title', existing_type=sa.VARCHAR(), nullable=True)
        batch_op.drop_column('is_search_active')

    op.drop_index('ix_scraper_erros_product_captured', table_name='scraper_errors')
    op.drop_index(op.f('ix_scraper_errors_id'), table_name='scraper_errors')
    op.drop_table('scraper_errors')
