"""Add payments and ledger tables

Revision ID: 004_add_payments_ledger_tables
Revises: 003_add_pac_and_governance_tables
Create Date: 2025-01-20 21:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004_add_payments_ledger_tables'
down_revision = '003_add_pac_and_governance_tables'
branch_labels = None
depends_on = None

def upgrade():
    # Create accounts table for double-entry ledger
    op.create_table('accounts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )
    
    # Create payments table
    op.create_table('payments',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('provider', sa.String(), nullable=False),
        sa.Column('provider_payment_id', sa.String(), nullable=True),
        sa.Column('amount', sa.BigInteger(), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('meta', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('provider_payment_id')
    )
    
    # Create refunds table
    op.create_table('refunds',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('payment_id', sa.BigInteger(), nullable=False),
        sa.Column('provider', sa.String(), nullable=False),
        sa.Column('provider_refund_id', sa.String(), nullable=True),
        sa.Column('amount', sa.BigInteger(), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['payment_id'], ['payments.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create fees table
    op.create_table('fees',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('payment_id', sa.BigInteger(), nullable=False),
        sa.Column('provider', sa.String(), nullable=False),
        sa.Column('amount', sa.BigInteger(), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False),
        sa.Column('detail', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['payment_id'], ['payments.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create entries table for double-entry bookkeeping
    op.create_table('entries',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('ts', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.BigInteger(), nullable=False),
        sa.Column('ref_type', sa.String(), nullable=False),
        sa.Column('ref_id', sa.BigInteger(), nullable=False),
        sa.Column('memo', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create payouts table
    op.create_table('payouts',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('provider', sa.String(), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False),
        sa.Column('amount', sa.BigInteger(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('method', sa.String(), nullable=False),
        sa.Column('scheduled_for', sa.DateTime(), nullable=True),
        sa.Column('executed_at', sa.DateTime(), nullable=True),
        sa.Column('external_ref', sa.String(), nullable=True),
        sa.Column('meta', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create provider_events table for webhook audit
    op.create_table('provider_events',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('provider', sa.String(), nullable=False),
        sa.Column('event_type', sa.String(), nullable=False),
        sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('signature_valid', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('received_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('provider_id', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for performance
    op.create_index('idx_payments_provider_id', 'payments', ['provider', 'provider_payment_id'])
    op.create_index('idx_payments_status', 'payments', ['status'])
    op.create_index('idx_entries_ref', 'entries', ['ref_type', 'ref_id'])
    op.create_index('idx_entries_account_ts', 'entries', ['account_id', 'ts'])
    op.create_index('idx_provider_events_provider_type', 'provider_events', ['provider', 'event_type'])
    op.create_index('idx_payouts_status', 'payouts', ['status'])

def downgrade():
    # Drop indexes
    op.drop_index('idx_payouts_status')
    op.drop_index('idx_provider_events_provider_type')
    op.drop_index('idx_entries_account_ts')
    op.drop_index('idx_entries_ref')
    op.drop_index('idx_payments_status')
    op.drop_index('idx_payments_provider_id')
    
    # Drop tables in reverse order
    op.drop_table('provider_events')
    op.drop_table('payouts')
    op.drop_table('entries')
    op.drop_table('fees')
    op.drop_table('refunds')
    op.drop_table('payments')
    op.drop_table('accounts')
