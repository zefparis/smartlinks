"""Add algorithm settings, AI policies and audit tables

Revision ID: 001_algorithm_settings
Revises: 
Create Date: 2025-08-20 02:12:48.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '001_algorithm_settings'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create algorithm_settings table
    op.create_table(
        'algorithm_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('algo_key', sa.String(50), nullable=False),
        sa.Column('settings_json', sa.JSON(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, default=1),
        sa.Column('updated_by', sa.String(100), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('algo_key', name='uq_algorithm_settings_algo_key')
    )
    
    # Create ai_policies table
    op.create_table(
        'ai_policies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('algo_key', sa.String(50), nullable=False),  # "global" for global policy
        sa.Column('authority', sa.Enum('advisory', 'safe_apply', 'full_control', name='authority_enum'), nullable=False, default='safe_apply'),
        sa.Column('risk_budget_daily', sa.Integer(), nullable=False, default=3),
        sa.Column('dry_run', sa.Boolean(), nullable=False, default=False),
        sa.Column('hard_guards_json', sa.JSON(), nullable=False),
        sa.Column('soft_guards_json', sa.JSON(), nullable=False),
        sa.Column('updated_by', sa.String(100), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('algo_key', name='uq_ai_policies_algo_key')
    )
    
    # Create audit_settings table
    op.create_table(
        'audit_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('algo_key', sa.String(50), nullable=False),
        sa.Column('actor', sa.String(100), nullable=False),
        sa.Column('diff_json', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for better performance
    op.create_index('ix_algorithm_settings_algo_key', 'algorithm_settings', ['algo_key'])
    op.create_index('ix_ai_policies_algo_key', 'ai_policies', ['algo_key'])
    op.create_index('ix_audit_settings_algo_key', 'audit_settings', ['algo_key'])
    op.create_index('ix_audit_settings_created_at', 'audit_settings', ['created_at'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_audit_settings_created_at', table_name='audit_settings')
    op.drop_index('ix_audit_settings_algo_key', table_name='audit_settings')
    op.drop_index('ix_ai_policies_algo_key', table_name='ai_policies')
    op.drop_index('ix_algorithm_settings_algo_key', table_name='algorithm_settings')
    
    # Drop tables
    op.drop_table('audit_settings')
    op.drop_table('ai_policies')
    op.drop_table('algorithm_settings')
    
    # Drop enum type
    op.execute("DROP TYPE IF EXISTS authority_enum")
