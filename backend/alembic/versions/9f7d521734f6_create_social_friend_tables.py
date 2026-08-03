"""create_social_friend_tables

Revision ID: 9f7d521734f6
Revises: 74dde4aede2b
Create Date: 2026-08-03 02:34:50.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '9f7d521734f6'
down_revision: Union[str, None] = '74dde4aede2b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('friend_requests',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('sender_id', sa.UUID(), nullable=False),
        sa.Column('receiver_id', sa.UUID(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='PENDING'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('responded_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['receiver_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['sender_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('sender_id', 'receiver_id', name='uq_friend_request_sender_receiver')
    )
    op.create_index(op.f('ix_friend_requests_receiver_id'), 'friend_requests', ['receiver_id'], unique=False)
    op.create_index(op.f('ix_friend_requests_sender_id'), 'friend_requests', ['sender_id'], unique=False)

    op.create_table('friendships',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('friend_id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['friend_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'friend_id', name='uq_friendship_user_friend')
    )
    op.create_index(op.f('ix_friendships_friend_id'), 'friendships', ['friend_id'], unique=False)
    op.create_index(op.f('ix_friendships_user_id'), 'friendships', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_friendships_user_id'), table_name='friendships')
    op.drop_index(op.f('ix_friendships_friend_id'), table_name='friendships')
    op.drop_table('friendships')
    op.drop_index(op.f('ix_friend_requests_sender_id'), table_name='friend_requests')
    op.drop_index(op.f('ix_friend_requests_receiver_id'), table_name='friend_requests')
    op.drop_table('friend_requests')
