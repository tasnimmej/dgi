from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
import datetime

class InvoiceModel(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False)
    ice_fournisseur = Column(String, index=True) # ICE du fournisseur ou client
    montant_ht = Column(Float, nullable=False)
    taux_tva = Column(Float, nullable=False)     # Ex: 0.20
    type_transaction = Column(String)           # "VENTE" ou "ACHAT"
    
    # Propriété calculée (stockée pour l'audit)
    montant_tva = Column(Float, nullable=False)
    montant_ttc = Column(Float, nullable=False)

class DeclarationModel(Base):
    __tablename__ = "declarations"

    id = Column(Integer, primary_key=True, index=True)
    company_ice = Column(String, index=True)  # Si un jour on gère plusieurs entreprises
    mois = Column(Integer, nullable=False)    # Ex: 1 pour Janvier
    annee = Column(Integer, nullable=False)   # Ex: 2026
    
    # Les résultats du calcul (identiques à ceux renvoyés par faire_bilan_tva)
    total_ht_ventes = Column(Float, nullable=False)
    total_tva_collectee = Column(Float, nullable=False)
    total_ht_achats = Column(Float, nullable=False)
    total_tva_deductible = Column(Float, nullable=False)
    tva_nette_a_payer = Column(Float, nullable=False)
    
    # Métadonnées
    date_creation = Column(DateTime, default=datetime.datetime.now)
    statut = Column(String, default="Brouillon") # "Brouillon", "Validée", "Payée"