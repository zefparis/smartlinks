"""Add algorithm_runs table

Revision ID: 004_add_algorithm_runs_table
Revises: 003_add_pac_and_governance_tables
Create Date: 2025-08-20 08:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004_add_algorithm_runs_table'
down_revision = '003_add_pac_and_governance_tables'
branch_labels = None
depends_on = None


def upgrade():
    # Create algorithm_runs table
    op.create_table('algorithm_runs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('algo_key', sa.String(50), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('settings_version', sa.Integer(), nullable=True),
        sa.Column('ai_authority_used', sa.String(50), nullable=True),
        sa.Column('risk_cost', sa.Integer(), nullable=True),
        sa.Column('rcp_applied', sa.Boolean(), nullable=False, default=False),
        sa.Column('error_message', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('ix_algorithm_runs_algo_key', 'algorithm_runs', ['algo_key'])
    op.create_index('ix_algorithm_runs_started_at', 'algorithm_runs', ['started_at'])
    
    # Update foreign key in rcp_evaluations table
    op.create_foreign_key(
        'fk_rcp_evaluations_algorithm_run', 
        'rcp_evaluations', 
        'algorithm_runs', 
        ['run_id'], 
        ['id']
    )


def downgrade():
    # Drop foreign key constraint
    op.drop_constraint('fk_rcp_evaluations_algorithm_run', 'rcp_evaluations', type_='foreignkey')
    
    # Drop indexes
    op.drop_index('ix_algorithm_runs_started_at', table_name='algorithm_runs')
    op.drop_index('ix_algorithm_runs_algo_key', table_name='algorithm_runs')
    
    # Drop table
    op.drop_table('algorithm_runs')
