"""add performance indexes to all models

Revision ID: a1b2c3d4e5f6
Revises: 3a4b275e5aeb
Create Date: 2026-08-29 12:18:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '3a4b275e5aeb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── messages table ─────────────────────────────────────────────────────
    op.create_index('ix_messages_session_id', 'messages', ['session_id'])
    op.create_index('ix_messages_created_at', 'messages', ['created_at'])
    op.create_index('ix_messages_session_created', 'messages', ['session_id', 'created_at'])

    # ── chat_sessions table ────────────────────────────────────────────────
    op.create_index('ix_chat_sessions_user_id', 'chat_sessions', ['user_id'])
    op.create_index('ix_chat_sessions_created_at', 'chat_sessions', ['created_at'])
    op.create_index('ix_chat_sessions_user_created', 'chat_sessions', ['user_id', 'created_at'])

    # ── feedback table ─────────────────────────────────────────────────────
    op.create_index('ix_feedback_rating', 'feedback', ['rating'])
    op.create_index('ix_feedback_created_at', 'feedback', ['created_at'])
    op.create_index('ix_feedback_rating_created', 'feedback', ['rating', 'created_at'])
    op.create_index('ix_feedback_user_message', 'feedback', ['user_id', 'message_id'], unique=True)

    # ── prompt_history table ───────────────────────────────────────────────
    op.create_index('ix_prompt_history_created_at', 'prompt_history', ['created_at'])

    # ── usage_logs table ───────────────────────────────────────────────────
    op.create_index('ix_usage_logs_endpoint', 'usage_logs', ['endpoint'])
    op.create_index('ix_usage_logs_created_at', 'usage_logs', ['created_at'])
    op.create_index('ix_usage_logs_endpoint_created', 'usage_logs', ['endpoint', 'created_at'])


def downgrade() -> None:
    # ── usage_logs table ───────────────────────────────────────────────────
    op.drop_index('ix_usage_logs_endpoint_created', 'usage_logs')
    op.drop_index('ix_usage_logs_created_at', 'usage_logs')
    op.drop_index('ix_usage_logs_endpoint', 'usage_logs')

    # ── prompt_history table ───────────────────────────────────────────────
    op.drop_index('ix_prompt_history_created_at', 'prompt_history')

    # ── feedback table ─────────────────────────────────────────────────────
    op.drop_index('ix_feedback_user_message', 'feedback')
    op.drop_index('ix_feedback_rating_created', 'feedback')
    op.drop_index('ix_feedback_created_at', 'feedback')
    op.drop_index('ix_feedback_rating', 'feedback')

    # ── chat_sessions table ────────────────────────────────────────────────
    op.drop_index('ix_chat_sessions_user_created', 'chat_sessions')
    op.drop_index('ix_chat_sessions_created_at', 'chat_sessions')
    op.drop_index('ix_chat_sessions_user_id', 'chat_sessions')

    # ── messages table ─────────────────────────────────────────────────────
    op.drop_index('ix_messages_session_created', 'messages')
    op.drop_index('ix_messages_created_at', 'messages')
    op.drop_index('ix_messages_session_id', 'messages')
