"""Add PaC and governance tables

Revision ID: 003_add_pac_and_governance_tables
Revises: 002_add_rcp_tables
Create Date: 2025-08-20 07:58:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003_add_pac_and_governance_tables'
down_revision = '002_add_rcp_tables'
branch_labels = None
depends_on = None


def upgrade():
    # PAC Plans table
    op.create_table('pac_plans',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('author', sa.String(), nullable=False),
        sa.Column('diff_json', sa.JSON(), nullable=False),
        sa.Column('dry_run', sa.Boolean(), nullable=False, default=True),
        sa.Column('status', sa.Enum('pending', 'applied', 'failed', name='pac_plan_status'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('applied_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_pac_plans_author'), 'pac_plans', ['author'], unique=False)
    op.create_index(op.f('ix_pac_plans_created_at'), 'pac_plans', ['created_at'], unique=False)

    # Approvals table
    op.create_table('approvals',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('algo_key', sa.String(), nullable=False),
        sa.Column('run_id', sa.String(), nullable=True),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('risk_cost', sa.Float(), nullable=False),
        sa.Column('actions_json', sa.JSON(), nullable=False),
        sa.Column('ctx_hash', sa.String(), nullable=False),
        sa.Column('status', sa.Enum('pending', 'approved', 'rejected', name='approval_status'), nullable=False),
        sa.Column('requested_by', sa.String(), nullable=False),
        sa.Column('decided_by', sa.String(), nullable=True),
        sa.Column('decided_at', sa.DateTime(), nullable=True),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_approvals_algo_key'), 'approvals', ['algo_key'], unique=False)
    op.create_index(op.f('ix_approvals_status'), 'approvals', ['status'], unique=False)
    op.create_index(op.f('ix_approvals_created_at'), 'approvals', ['created_at'], unique=False)

    # Feature Snapshots table
    op.create_table('feature_snapshots',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('ts', sa.DateTime(), nullable=False),
        sa.Column('key', sa.String(), nullable=False),
        sa.Column('value_json', sa.JSON(), nullable=False),
        sa.Column('source', sa.String(), nullable=False),
        sa.Column('tenant_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_feature_snapshots_ts_key'), 'feature_snapshots', ['ts', 'key'], unique=False)
    op.create_index(op.f('ix_feature_snapshots_tenant_id'), 'feature_snapshots', ['tenant_id'], unique=False)

    # Policy Rollouts table
    op.create_table('policy_rollouts',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('policy_id', sa.String(), nullable=False),
        sa.Column('from_percent', sa.Float(), nullable=False),
        sa.Column('to_percent', sa.Float(), nullable=False),
        sa.Column('state', sa.Enum('pending', 'active', 'completed', 'rolled_back', name='rollout_state'), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('auto_rollback_rule', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_policy_rollouts_policy_id'), 'policy_rollouts', ['policy_id'], unique=False)
    op.create_index(op.f('ix_policy_rollouts_state'), 'policy_rollouts', ['state'], unique=False)

    # Add tenant_id to existing tables (nullable for backward compatibility)
    op.add_column('rcp_policies', sa.Column('tenant_id', sa.String(), nullable=True))
    op.add_column('rcp_evaluations', sa.Column('tenant_id', sa.String(), nullable=True))
    op.create_index(op.f('ix_rcp_policies_tenant_id'), 'rcp_policies', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_rcp_evaluations_tenant_id'), 'rcp_evaluations', ['tenant_id'], unique=False)

    # Add foreign key constraint for policy rollouts
    op.create_foreign_key('fk_policy_rollouts_policy_id', 'policy_rollouts', 'rcp_policies', ['policy_id'], ['id'])


def downgrade():
    # Drop foreign key constraints
    op.drop_constraint('fk_policy_rollouts_policy_id', 'policy_rollouts', type_='foreignkey')
    
    # Drop indexes
    op.drop_index(op.f('ix_rcp_evaluations_tenant_id'), table_name='rcp_evaluations')
    op.drop_index(op.f('ix_rcp_policies_tenant_id'), table_name='rcp_policies')
    op.drop_index(op.f('ix_policy_rollouts_state'), table_name='policy_rollouts')
    op.drop_index(op.f('ix_policy_rollouts_policy_id'), table_name='policy_rollouts')
    op.drop_index(op.f('ix_feature_snapshots_tenant_id'), table_name='feature_snapshots')
    op.drop_index(op.f('ix_feature_snapshots_ts_key'), table_name='feature_snapshots')
    op.drop_index(op.f('ix_approvals_created_at'), table_name='approvals')
    op.drop_index(op.f('ix_approvals_status'), table_name='approvals')
    op.drop_index(op.f('ix_approvals_algo_key'), table_name='approvals')
    op.drop_index(op.f('ix_pac_plans_created_at'), table_name='pac_plans')
    op.drop_index(op.f('ix_pac_plans_author'), table_name='pac_plans')
    
    # Drop columns
    op.drop_column('rcp_evaluations', 'tenant_id')
    op.drop_column('rcp_policies', 'tenant_id')
    
    # Drop tables
    op.drop_table('policy_rollouts')
    op.drop_table('feature_snapshots')
    op.drop_table('approvals')
    op.drop_table('pac_plans')
    
    # Drop enums
    op.execute('DROP TYPE rollout_state')
    op.execute('DROP TYPE approval_status')
    op.execute('DROP TYPE pac_plan_status')
