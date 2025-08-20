"""Add RCP (Runtime Control Policies) tables

Revision ID: 002_add_rcp_tables
Revises: 001_add_algorithm_settings_tables
Create Date: 2025-01-20 02:53:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_add_rcp_tables'
down_revision = '001_add_algorithm_settings_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create rcp_policies table
    op.create_table(
        'rcp_policies',
        sa.Column('id', sa.String(255), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('scope', sa.Enum('global', 'algorithm', 'segment', name='rcp_scope'), nullable=False, default='global'),
        sa.Column('algo_key', sa.String(100), nullable=True),
        sa.Column('selector_json', postgresql.JSONB(), nullable=True),
        sa.Column('mode', sa.Enum('monitor', 'enforce', name='rcp_mode'), nullable=False, default='enforce'),
        sa.Column('authority_required', sa.Enum('operator', 'admin', 'dg_ai', name='rcp_authority'), nullable=False, default='dg_ai'),
        sa.Column('hard_guards_json', postgresql.JSONB(), nullable=True),
        sa.Column('soft_guards_json', postgresql.JSONB(), nullable=True),
        sa.Column('limits_json', postgresql.JSONB(), nullable=True),
        sa.Column('gates_json', postgresql.JSONB(), nullable=True),
        sa.Column('mutations_json', postgresql.JSONB(), nullable=True),
        sa.Column('schedule_cron', sa.String(100), nullable=True),
        sa.Column('rollout_percent', sa.Float(), nullable=False, default=1.0),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('enabled', sa.Boolean(), nullable=False, default=True),
        sa.Column('version', sa.Integer(), nullable=False, default=1),
        sa.Column('updated_by', sa.String(100), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )
    
    # Create indexes for rcp_policies
    op.create_index('idx_rcp_policies_scope_algo', 'rcp_policies', ['scope', 'algo_key'])
    op.create_index('idx_rcp_policies_enabled', 'rcp_policies', ['enabled'])
    op.create_index('idx_rcp_policies_expires', 'rcp_policies', ['expires_at'])
    
    # Create rcp_evaluations table
    op.create_table(
        'rcp_evaluations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('policy_id', sa.String(255), sa.ForeignKey('rcp_policies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('algo_key', sa.String(100), nullable=False),
        sa.Column('run_id', sa.String(36), nullable=True),  # FK to algorithm_runs when available
        sa.Column('result', sa.Enum('allowed', 'modified', 'blocked', 'mixed', name='rcp_result'), nullable=False),
        sa.Column('stats_json', postgresql.JSONB(), nullable=True),
        sa.Column('diff_json', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )
    
    # Create indexes for rcp_evaluations
    op.create_index('idx_rcp_evaluations_policy', 'rcp_evaluations', ['policy_id'])
    op.create_index('idx_rcp_evaluations_algo_time', 'rcp_evaluations', ['algo_key', 'created_at'])
    op.create_index('idx_rcp_evaluations_run', 'rcp_evaluations', ['run_id'])
    
    # Add new columns to algorithm_runs table (if it exists)
    try:
        op.add_column('algorithm_runs', sa.Column('settings_version', sa.Integer(), nullable=True))
        op.add_column('algorithm_runs', sa.Column('ai_authority_used', sa.String(50), nullable=True))
        op.add_column('algorithm_runs', sa.Column('risk_cost', sa.Float(), nullable=True, default=0.0))
        op.add_column('algorithm_runs', sa.Column('rcp_applied', sa.Boolean(), nullable=False, default=False))
    except Exception:
        # Table might not exist yet, that's OK
        pass


def downgrade() -> None:
    # Remove columns from algorithm_runs
    try:
        op.drop_column('algorithm_runs', 'rcp_applied')
        op.drop_column('algorithm_runs', 'risk_cost')
        op.drop_column('algorithm_runs', 'ai_authority_used')
        op.drop_column('algorithm_runs', 'settings_version')
    except Exception:
        pass
    
    # Drop indexes and tables
    op.drop_index('idx_rcp_evaluations_run')
    op.drop_index('idx_rcp_evaluations_algo_time')
    op.drop_index('idx_rcp_evaluations_policy')
    op.drop_table('rcp_evaluations')
    
    op.drop_index('idx_rcp_policies_expires')
    op.drop_index('idx_rcp_policies_enabled')
    op.drop_index('idx_rcp_policies_scope_algo')
    op.drop_table('rcp_policies')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS rcp_result')
    op.execute('DROP TYPE IF EXISTS rcp_authority')
    op.execute('DROP TYPE IF EXISTS rcp_mode')
    op.execute('DROP TYPE IF EXISTS rcp_scope')
