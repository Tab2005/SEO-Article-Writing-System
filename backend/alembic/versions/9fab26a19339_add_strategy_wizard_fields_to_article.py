"""Initial database schema with strategy wizard fields

Revision ID: 9fab26a19339
Revises: 
Create Date: 2026-01-13 19:49:48.018943

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9fab26a19339'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('username', sa.String(50), nullable=True),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_superuser', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)

    # Create projects table
    op.create_table('projects',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('owner_id', sa.String(36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_projects_id'), 'projects', ['id'], unique=False)
    op.create_index(op.f('ix_projects_owner_id'), 'projects', ['owner_id'], unique=False)

    # Create articles table
    op.create_table('articles',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('outline', sa.Text(), nullable=True),
        sa.Column('status', sa.String(50), nullable=True),
        sa.Column('version', sa.Integer(), nullable=True),
        sa.Column('project_id', sa.String(36), nullable=False),
        sa.Column('parent_version_id', sa.String(36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('strategy_config', sa.JSON(), nullable=True),
        sa.Column('research_job_id', sa.String(36), nullable=True),
        sa.Column('wizard_step', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['parent_version_id'], ['articles.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_articles_id'), 'articles', ['id'], unique=False)
    op.create_index(op.f('ix_articles_parent_version_id'), 'articles', ['parent_version_id'], unique=False)
    op.create_index(op.f('ix_articles_project_id'), 'articles', ['project_id'], unique=False)
    op.create_index(op.f('ix_articles_research_job_id'), 'articles', ['research_job_id'], unique=False)

    # Create search_cache table
    op.create_table('search_cache',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('query_hash', sa.String(64), nullable=False),
        sa.Column('keyword', sa.String(255), nullable=False),
        sa.Column('market', sa.String(10), nullable=False),
        sa.Column('results', sa.JSON(), nullable=False),
        sa.Column('cached_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_search_cache_id'), 'search_cache', ['id'], unique=False)
    op.create_index(op.f('ix_search_cache_query_hash'), 'search_cache', ['query_hash'], unique=True)

    # Create research_jobs table
    op.create_table('research_jobs',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('keyword', sa.String(255), nullable=False),
        sa.Column('market', sa.String(10), nullable=False),
        sa.Column('depth', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('progress', sa.Integer(), nullable=True),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('user_id', sa.String(36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_research_jobs_id'), 'research_jobs', ['id'], unique=False)
    op.create_index(op.f('ix_research_jobs_user_id'), 'research_jobs', ['user_id'], unique=False)

    # Create research_competitors table
    op.create_table('research_competitors',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('job_id', sa.String(36), nullable=False),
        sa.Column('rank', sa.Integer(), nullable=False),
        sa.Column('url', sa.String(2000), nullable=False),
        sa.Column('serp_title', sa.Text(), nullable=True),
        sa.Column('snippet', sa.Text(), nullable=True),
        sa.Column('serp_fetched_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('fetch_status', sa.String(50), nullable=True),
        sa.Column('page_title', sa.Text(), nullable=True),
        sa.Column('meta_description', sa.Text(), nullable=True),
        sa.Column('meta_keywords', sa.Text(), nullable=True),
        sa.Column('headings', sa.JSON(), nullable=True),
        sa.Column('word_count', sa.Integer(), nullable=True),
        sa.Column('content_text', sa.Text(), nullable=True),
        sa.Column('content_hash', sa.String(64), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('scraped_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['job_id'], ['research_jobs.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_research_competitors_id'), 'research_competitors', ['id'], unique=False)
    op.create_index(op.f('ix_research_competitors_job_id'), 'research_competitors', ['job_id'], unique=False)

    # Create research_artifacts table
    op.create_table('research_artifacts',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('job_id', sa.String(36), nullable=False),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['job_id'], ['research_jobs.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_research_artifacts_id'), 'research_artifacts', ['id'], unique=False)
    op.create_index(op.f('ix_research_artifacts_job_id'), 'research_artifacts', ['job_id'], unique=False)
    op.create_index(op.f('ix_research_artifacts_type'), 'research_artifacts', ['type'], unique=False)


def downgrade() -> None:
    # Remove all tables in reverse order
    op.drop_table('research_artifacts')
    op.drop_table('research_competitors')
    op.drop_table('research_jobs')
    op.drop_table('search_cache')
    op.drop_table('articles')
    op.drop_table('projects')
    op.drop_table('users')
