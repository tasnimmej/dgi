from app.services.calculator import calculer_tva_facture, faire_bilan_tva


def test_calculer_tva_facture():
    res = calculer_tva_facture(100.0, 0.2)
    assert res['montant_tva'] == 20.0
    assert res['montant_ttc'] == 120.0


def test_faire_bilan_tva():
    factures = [
        {"montant_ht": 100.0, "taux_tva": 0.2, "type_transaction": "VENTE"},
        {"montant_ht": 50.0, "taux_tva": 0.2, "type_transaction": "ACHAT"}
    ]
    bilan = faire_bilan_tva(factures)
    assert bilan['total_ht_ventes'] == 100.0
    assert bilan['total_tva_collectee'] == 20.0
    assert bilan['total_ht_achats'] == 50.0
    assert bilan['total_tva_deductible'] == 10.0
    assert bilan['tva_nette_a_payer'] == 10.0
