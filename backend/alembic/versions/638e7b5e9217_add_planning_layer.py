"""add_planning_layer

Revision ID: 638e7b5e9217
Revises: 9fab26a19339
Create Date: 2026-05-22 13:18:18.308315

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import Text
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '638e7b5e9217'
down_revision: Union[str, None] = '9fab26a19339'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create site_profiles table
    op.create_table('site_profiles',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('project_id', sa.UUID(), nullable=False),
        sa.Column('site_name', sa.String(length=255), nullable=False),
        sa.Column('business_type', sa.String(length=255), nullable=True),
        sa.Column('site_description', sa.Text(), nullable=True),
        sa.Column('target_audiences', sa.JSON(), nullable=True),
        sa.Column('products_or_services', sa.JSON(), nullable=True),
        sa.Column('core_topics', sa.JSON(), nullable=True),
        sa.Column('allowed_angles', sa.JSON(), nullable=True),
        sa.Column('restricted_angles', sa.JSON(), nullable=True),
        sa.Column('brand_voice', sa.Text(), nullable=True),
        sa.Column('proof_assets', sa.JSON(), nullable=True),
        sa.Column('primary_goals', sa.JSON(), nullable=True),
        sa.Column('geo_focus', sa.JSON(), nullable=True),
        sa.Column('industry_constraints', sa.JSON(), nullable=True),
        sa.Column('editorial_notes', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('summary_snapshot', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_id')
    )
    op.create_index(op.f('ix_site_profiles_project_id'), 'site_profiles', ['project_id'], unique=True)

    # 2. Create topic_nodes table
    op.create_table('topic_nodes',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('project_id', sa.UUID(), nullable=False),
        sa.Column('parent_id', sa.UUID(), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('topic_role', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('journey_stage', sa.String(length=50), nullable=True),
        sa.Column('priority', sa.String(length=50), nullable=False),
        sa.Column('supports', sa.JSON(), nullable=True),
        sa.Column('supported_by', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['parent_id'], ['topic_nodes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_topic_nodes_parent_id'), 'topic_nodes', ['parent_id'], unique=False)
    op.create_index(op.f('ix_topic_nodes_project_id'), 'topic_nodes', ['project_id'], unique=False)

    # 3. Create content_items table
    op.create_table('content_items',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('project_id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(length=512), nullable=False),
        sa.Column('url', sa.String(length=1024), nullable=True),
        sa.Column('content_type', sa.String(length=50), nullable=False),
        sa.Column('mapped_topic_id', sa.UUID(), nullable=True),
        sa.Column('journey_stage', sa.String(length=50), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['mapped_topic_id'], ['topic_nodes.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_content_items_mapped_topic_id'), 'content_items', ['mapped_topic_id'], unique=False)
    op.create_index(op.f('ix_content_items_project_id'), 'content_items', ['project_id'], unique=False)

    # 4. Create qualification_results table
    op.create_table('qualification_results',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('project_id', sa.UUID(), nullable=False),
        sa.Column('input_term', sa.String(length=255), nullable=False),
        sa.Column('decision', sa.String(length=50), nullable=False),
        sa.Column('summary_reason', sa.Text(), nullable=True),
        sa.Column('mapped_topic_id', sa.UUID(), nullable=True),
        sa.Column('suggested_angle', sa.Text(), nullable=True),
        sa.Column('target_journey_stage', sa.String(length=50), nullable=True),
        sa.Column('identity_fit', sa.String(length=50), nullable=True),
        sa.Column('topic_fit', sa.String(length=50), nullable=True),
        sa.Column('audience_fit', sa.String(length=50), nullable=True),
        sa.Column('authority_fit', sa.String(length=50), nullable=True),
        sa.Column('business_fit', sa.String(length=50), nullable=True),
        sa.Column('overlap_risk', sa.String(length=50), nullable=True),
        sa.Column('boundary_risk', sa.String(length=50), nullable=True),
        sa.Column('risks', sa.JSON(), nullable=True),
        sa.Column('alternative_topics', sa.JSON(), nullable=True),
        sa.Column('recommended_next_step', sa.Text(), nullable=True),
        sa.Column('review_status', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['mapped_topic_id'], ['topic_nodes.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_qualification_results_mapped_topic_id'), 'qualification_results', ['mapped_topic_id'], unique=False)
    op.create_index(op.f('ix_qualification_results_project_id'), 'qualification_results', ['project_id'], unique=False)

    # 5. Add columns to projects table
    op.add_column('projects', sa.Column('target_market', sa.String(length=10), nullable=False, server_default='tw'))
    op.add_column('projects', sa.Column('mode', sa.String(length=50), nullable=False, server_default='existing_site'))
    op.add_column('projects', sa.Column('status', sa.String(length=50), nullable=False, server_default='draft'))
    op.add_column('projects', sa.Column('domain', sa.String(length=255), nullable=True))

    # 6. Add columns to articles table (excluding 'slug' and 'target_keyword' which already exist)
    op.add_column('articles', sa.Column('secondary_keywords', sa.JSON(), nullable=True))
    op.add_column('articles', sa.Column('meta_description', sa.String(length=500), nullable=True))
    op.add_column('articles', sa.Column('word_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('articles', sa.Column('published_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    # Remove columns from articles table
    op.drop_column('articles', 'published_at')
    op.drop_column('articles', 'word_count')
    op.drop_column('articles', 'meta_description')
    op.drop_column('articles', 'secondary_keywords')

    # Remove columns from projects table
    op.drop_column('projects', 'domain')
    op.drop_column('projects', 'status')
    op.drop_column('projects', 'mode')
    op.drop_column('projects', 'target_market')

    # Drop tables
    op.drop_index(op.f('ix_qualification_results_project_id'), table_name='qualification_results')
    op.drop_index(op.f('ix_qualification_results_mapped_topic_id'), table_name='qualification_results')
    op.drop_table('qualification_results')

    op.drop_index(op.f('ix_content_items_project_id'), table_name='content_items')
    op.drop_index(op.f('ix_content_items_mapped_topic_id'), table_name='content_items')
    op.drop_table('content_items')

    op.drop_index(op.f('ix_topic_nodes_project_id'), table_name='topic_nodes')
    op.drop_index(op.f('ix_topic_nodes_parent_id'), table_name='topic_nodes')
    op.drop_table('topic_nodes')

    op.drop_index(op.f('ix_site_profiles_project_id'), table_name='site_profiles')
    op.drop_table('site_profiles')
