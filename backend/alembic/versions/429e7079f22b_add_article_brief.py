"""add_article_brief

Revision ID: 429e7079f22b
Revises: 638e7b5e9217
Create Date: 2026-05-22 13:51:01.969541

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '429e7079f22b'
down_revision: Union[str, None] = '638e7b5e9217'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create article_briefs table
    op.create_table('article_briefs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('project_id', sa.UUID(), nullable=False),
        sa.Column('qualification_id', sa.UUID(), nullable=True),
        sa.Column('mapped_topic_id', sa.UUID(), nullable=True),
        sa.Column('title_direction', sa.String(length=500), nullable=False),
        sa.Column('article_role', sa.String(length=50), nullable=True),
        sa.Column('search_intent', sa.String(length=255), nullable=True),
        sa.Column('target_audience', sa.String(length=500), nullable=True),
        sa.Column('primary_question', sa.Text(), nullable=True),
        sa.Column('next_question', sa.Text(), nullable=True),
        sa.Column('info_gain_requirement', sa.Text(), nullable=True),
        sa.Column('restricted_content', sa.Text(), nullable=True),
        sa.Column('recommended_internal_links', sa.Text(), nullable=True),
        sa.Column('cta_direction', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='draft'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['mapped_topic_id'], ['topic_nodes.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['qualification_id'], ['qualification_results.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_article_briefs_mapped_topic_id'), 'article_briefs', ['mapped_topic_id'], unique=False)
    op.create_index(op.f('ix_article_briefs_project_id'), 'article_briefs', ['project_id'], unique=False)
    op.create_index(op.f('ix_article_briefs_qualification_id'), 'article_briefs', ['qualification_id'], unique=False)

    # 2. Add brief_id to articles
    op.add_column('articles', sa.Column('brief_id', sa.UUID(), nullable=True))
    op.create_index(op.f('ix_articles_brief_id'), 'articles', ['brief_id'], unique=False)


def downgrade() -> None:
    # 1. Remove brief_id from articles
    op.drop_index(op.f('ix_articles_brief_id'), table_name='articles')
    op.drop_column('articles', 'brief_id')

    # 2. Drop article_briefs table
    op.drop_index(op.f('ix_article_briefs_qualification_id'), table_name='article_briefs')
    op.drop_index(op.f('ix_article_briefs_project_id'), table_name='article_briefs')
    op.drop_index(op.f('ix_article_briefs_mapped_topic_id'), table_name='article_briefs')
    op.drop_table('article_briefs')
