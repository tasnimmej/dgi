from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.colors import black, white, HexColor
from reportlab.lib.utils import simpleSplit
import os

def generer_declaration_pdf(declaration_data: dict, output_path: str):
    """
    Génère un PDF ressemblant au formulaire de déclaration de TVA marocain.
    """
    # Création du canvas
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4
    
    # --- En-tête (Logo et titres) ---
    c.setFont("Helvetica-Bold", 16)
    c.drawString(20*mm, height - 20*mm, "DIRECTION GÉNÉRALE DES IMPÔTS")
    c.setFont("Helvetica", 12)
    c.drawString(20*mm, height - 25*mm, "DÉCLARATION MENSUELLE DE LA TAXE SUR LA VALEUR AJOUTÉE (TVA)")
    
    # Ligne de séparation
    c.line(20*mm, height - 30*mm, width - 20*mm, height - 30*mm)
    
    # --- Informations de l'entreprise ---
    c.setFont("Helvetica-Bold", 11)
    c.drawString(20*mm, height - 40*mm, "IDENTIFICATION DE L'ENTREPRISE")
    c.setFont("Helvetica", 10)
    c.drawString(20*mm, height - 45*mm, f"ICE : {declaration_data['company_ice']}")
    c.drawString(20*mm, height - 50*mm, f"Période concernée : {declaration_data['mois']:02d}/{declaration_data['annee']}")
    c.drawString(20*mm, height - 55*mm, f"Date de création : {declaration_data['date_creation']}")
    
    # --- Tableau des montants ---
    # Titres du tableau
    c.setFont("Helvetica-Bold", 9)
    y_position = height - 75*mm
    
    # Dessin des en-têtes de colonnes (grille)
    c.rect(20*mm, y_position - 5*mm, 80*mm, 10*mm) # Colonne Libellé
    c.rect(100*mm, y_position - 5*mm, 50*mm, 10*mm) # Colonne Montant HT
    c.rect(150*mm, y_position - 5*mm, 50*mm, 10*mm) # Colonne TVA
    c.rect(200*mm, y_position - 5*mm, 50*mm, 10*mm) # Colonne TTC
    
    # Textes des colonnes
    c.drawString(22*mm, y_position, "Libellé")
    c.drawString(105*mm, y_position, "Montant HT")
    c.drawString(155*mm, y_position, "TVA")
    c.drawString(205*mm, y_position, "TTC")
    
    # Lignes de données (Ventes)
    y_position -= 15*mm
    c.setFont("Helvetica", 9)
    
    # Ventes
    c.rect(20*mm, y_position - 5*mm, 80*mm, 10*mm)
    c.rect(100*mm, y_position - 5*mm, 50*mm, 10*mm)
    c.rect(150*mm, y_position - 5*mm, 50*mm, 10*mm)
    c.rect(200*mm, y_position - 5*mm, 50*mm, 10*mm)
    c.drawString(22*mm, y_position, "Ventes du mois")
    c.drawString(105*mm, y_position, f"{declaration_data['total_ht_ventes']:.2f}")
    c.drawString(155*mm, y_position, f"{declaration_data['total_tva_collectee']:.2f}")
    c.drawString(205*mm, y_position, f"{declaration_data['total_ht_ventes'] + declaration_data['total_tva_collectee']:.2f}")
    
    # Achats
    y_position -= 15*mm
    c.rect(20*mm, y_position - 5*mm, 80*mm, 10*mm)
    c.rect(100*mm, y_position - 5*mm, 50*mm, 10*mm)
    c.rect(150*mm, y_position - 5*mm, 50*mm, 10*mm)
    c.rect(200*mm, y_position - 5*mm, 50*mm, 10*mm)
    c.drawString(22*mm, y_position, "Achats du mois")
    c.drawString(105*mm, y_position, f"{declaration_data['total_ht_achats']:.2f}")
    c.drawString(155*mm, y_position, f"{declaration_data['total_tva_deductible']:.2f}")
    c.drawString(205*mm, y_position, f"{declaration_data['total_ht_achats'] + declaration_data['total_tva_deductible']:.2f}")
    
    # --- Total (TVA Nette à Payer) ---
    y_position -= 20*mm
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(HexColor('#D32F2F')) # Rouge foncé pour le résultat
    c.rect(100*mm, y_position - 5*mm, 150*mm, 15*mm, fill=1, stroke=0) # Rectangle rouge clair
    c.setFillColor(white)
    c.drawString(105*mm, y_position + 3*mm, f"TVA NETTE À PAYER : {declaration_data['tva_nette_a_payer']:.2f} MAD")
    c.setFillColor(black)
    
    # --- Pied de page (Signature et mentions légales) ---
    c.setFont("Helvetica", 8)
    y_position -= 40*mm
    c.line(20*mm, y_position, width - 20*mm, y_position)
    c.drawString(20*mm, y_position - 5*mm, "Document généré automatiquement par le Système de Déclaration DGI - PME.")
    c.drawString(20*mm, y_position - 10*mm, "Cachet de l'entreprise : ___________________________")
    c.drawString(20*mm, y_position - 15*mm, "Date de signature : ___________________________")
    
    # --- Sauvegarde ---
    c.save()
    return output_path