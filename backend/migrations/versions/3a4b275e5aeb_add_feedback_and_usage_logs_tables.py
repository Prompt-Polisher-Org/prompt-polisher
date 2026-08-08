"""Add feedback and usage_logs tables

Revision ID: 3a4b275e5aeb
Revises: 6dfbd0bc9489
Create Date: 2026-08-07 01:02:09.410162

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3a4b275e5aeb'
down_revision: Union[str, Sequence[str], None] = '6dfbd0bc9489'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('feedback',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('message_id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['message_id'], ['messages.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_feedback_message_id'), 'feedback', ['message_id'], unique=False)
    op.create_index(op.f('ix_feedback_user_id'), 'feedback', ['user_id'], unique=False)

    op.create_table('usage_logs',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=True),
        sa.Column('endpoint', sa.String(length=255), nullable=False),
        sa.Column('tokens_used', sa.Integer(), nullable=True),
        sa.Column('duration_ms', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_usage_logs_user_id'), 'usage_logs', ['user_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_usage_logs_user_id'), table_name='usage_logs')
    op.drop_table('usage_logs')
    op.drop_index(op.f('ix_feedback_user_id'), table_name='feedback')
    op.drop_index(op.f('ix_feedback_message_id'), table_name='feedback')
    op.drop_table('feedback')
