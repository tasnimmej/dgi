"""initial migration
Revision ID: 0001_initial
Revises: 
Create Date: 2026-08-11
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated ###
    op.create_table('companies',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('ice', sa.String(), nullable=False, unique=True),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('address', sa.String(), nullable=True),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('phone', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )

    op.create_table('users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('email', sa.String(), nullable=False, unique=True),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('full_name', sa.String(), nullable=True),
        sa.Column('role', sa.String(), nullable=True),
        sa.Column('company_id', sa.Integer(), sa.ForeignKey('companies.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )

    op.create_table('invoices',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('date', sa.Date(), nullable=True),
        sa.Column('ice_fournisseur', sa.String(), nullable=True),
        sa.Column('montant_ht', sa.Float(), nullable=False),
        sa.Column('taux_tva', sa.Float(), nullable=False),
        sa.Column('type_transaction', sa.String(), nullable=True),
        sa.Column('company_id', sa.Integer(), sa.ForeignKey('companies.id'), nullable=True),
        sa.Column('montant_tva', sa.Float(), nullable=False),
        sa.Column('montant_ttc', sa.Float(), nullable=False),
    )

    op.create_table('declarations',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('company_ice', sa.String(), nullable=True),
        sa.Column('mois', sa.Integer(), nullable=False),
        sa.Column('annee', sa.Integer(), nullable=False),
        sa.Column('total_ht_ventes', sa.Float(), nullable=False),
        sa.Column('total_tva_collectee', sa.Float(), nullable=False),
        sa.Column('total_ht_achats', sa.Float(), nullable=False),
        sa.Column('total_tva_deductible', sa.Float(), nullable=False),
        sa.Column('tva_nette_a_payer', sa.Float(), nullable=False),
        sa.Column('date_creation', sa.DateTime(), nullable=True),
        sa.Column('statut', sa.String(), nullable=True),
    )
    # ### end Alembic commands ###


def downgrade():
    op.drop_table('declarations')
    op.drop_table('invoices')
    op.drop_table('users')
    op.drop_table('companies')
