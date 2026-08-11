def calculer_tva_facture(montant_ht: float, taux_tva: float):
    """
    Calcule la TVA et le TTC de manière absolument fiable.
    Retourne un dictionnaire.
    """
    tva = round(montant_ht * taux_tva, 2)
    ttc = round(montant_ht + tva, 2)
    return {"montant_tva": tva, "montant_ttc": ttc}

def faire_bilan_tva(liste_factures):
    """
    Prend une liste de factures (format JSON) et calcule la TVA globale.
    """
    total_tva_collectee = 0.0
    total_tva_deductible = 0.0
    total_ht_ventes = 0.0
    total_ht_achats = 0.0

    for facture in liste_factures:
        # On recalcul proprement la TVA avec notre fonction sécurisée
        montants = calculer_tva_facture(facture["montant_ht"], facture["taux_tva"])
        
        # On ajoute les valeurs au bon endroit selon le type de transaction
        if facture["type_transaction"].upper() == "VENTE":
            total_tva_collectee += montants["montant_tva"]
            total_ht_ventes += facture["montant_ht"]
        elif facture["type_transaction"].upper() == "ACHAT":
            total_tva_deductible += montants["montant_tva"]
            total_ht_achats += facture["montant_ht"]
            
    # Calcul final
    tva_nette_a_payer = round(total_tva_collectee - total_tva_deductible, 2)

    return {
        "total_ht_ventes": round(total_ht_ventes, 2),
        "total_tva_collectee": round(total_tva_collectee, 2),
        "total_ht_achats": round(total_ht_achats, 2),
        "total_tva_deductible": round(total_tva_deductible, 2),
        "tva_nette_a_payer": tva_nette_a_payer
    }