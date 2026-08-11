from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.services.notifications import envoyer_email_alerte
from sqlalchemy.orm import Session
from app.models import DeclarationModel
from datetime import datetime, timedelta

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from sqlalchemy import extract
from datetime import datetime
from app.models import DeclarationModel

import pandas as pd
import io

from app.database import SessionLocal, engine, Base
from app.models import InvoiceModel
from app.services.calculator import (
    faire_bilan_tva,
    calculer_tva_facture
)

# ============================================================
# IMPORTS POUR LE PDF (NOUVEAU)
# ============================================================
from app.services.pdf_generator import generer_declaration_pdf
from fastapi.responses import FileResponse
import os


# ============================================================
# CRÉATION DES TABLES
# ============================================================

Base.metadata.create_all(bind=engine)


# ============================================================
# APPLICATION FASTAPI
# ============================================================

app = FastAPI(
    title="Système de Déclaration DGI - API"
)

# === Auth router ===
from app.auth import router as auth_router
app.include_router(auth_router, prefix="/auth", tags=["auth"])


# ============================================================
# CORS
# Autorise le frontend Vite/React sur le port 5173
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# SESSION BASE DE DONNÉES
# ============================================================

def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()

# ============================================================
# PLANIFICATEUR DE TÂCHES (BACKGROUND SCHEDULER)
# Vérifie les échéances tous les jours à 9h00 du matin
# ============================================================

def verifier_echeances():
    """
    Fonction exécutée automatiquement par le scheduler.
    Elle vérifie dans la base de données les déclarations dont l'échéance approche.
    """
    print("🔍 [Scheduler] Vérification des échéances fiscales en cours...")
    
    # On crée une session de base de données pour cette tâche
    db = SessionLocal()
    try:
        aujourd_hui = datetime.now().date()
        
        # Récupérer toutes les déclarations validées
        declarations = db.query(DeclarationModel).filter(DeclarationModel.statut == "Validée").all()
        
        for dec in declarations:
            # Calcul de la date d'échéance (le 20 du mois suivant)
            # Exemple: Si mois=1 (Janvier), échéance = 20/02/2026
            if dec.mois == 12:
                mois_echeance = 1
                annee_echeance = dec.annee + 1
            else:
                mois_echeance = dec.mois + 1
                annee_echeance = dec.annee
            
            # On crée une date d'échéance (20 du mois suivant)
            date_echeance = datetime(annee_echeance, mois_echeance, 20).date()
            
            # Calcul de l'écart en jours
            jours_restants = (date_echeance - aujourd_hui).days
            
            # Si on est à J-3, on envoie une alerte
            if jours_restants == 3:
                message = (
                    f"⚠️ ALERTE FISCALE - PME\n\n"
                    f"Bonjour,\n\n"
                    f"Votre déclaration de TVA pour le mois de {dec.mois}/{dec.annee} "
                    f"est due dans 3 jours (le {date_echeance.strftime('%d/%m/%Y')}).\n"
                    f"Montant à payer : {dec.tva_nette_a_payer} MAD.\n\n"
                    f"Merci de régulariser votre situation avant cette date pour éviter les pénalités."
                )
                
                # Envoi de l'email (ou simulation si pas configuré)
                # Dans un vrai projet, on récupérera l'email depuis la table Company
                print(f"📧 [SIMULATION] Email envoyé pour la déclaration {dec.mois}/{dec.annee} : \n{message}")
                
                # Si vous aviez un email configuré, vous décommentez la ligne ci-dessous :
                # envoyer_email_alerte("client@pmemaroc.ma", "Échéance TVA imminente", message)

    except Exception as e:
        print(f"❌ Erreur dans le scheduler : {e}")
    finally:
        db.close()

scheduler = BackgroundScheduler(timezone="Africa/Casablanca")

scheduler.add_job(
    verifier_echeances,
    trigger=CronTrigger(
        hour=9,
        minute=0,
        timezone="Africa/Casablanca"
    ),
    id="verification_echeances",
    replace_existing=True
)

scheduler.start()

# Avertissement pour fermer le scheduler proprement à la fermeture de l'API
import atexit
atexit.register(lambda: scheduler.shutdown())

# ============================================================
# ROUTE PRINCIPALE
# ============================================================

@app.get("/")
def read_root():
    return {
        "message": "L'API de déclaration fiscale est opérationnelle !"
    }


# ============================================================
# IMPORT CSV
# ============================================================

@app.post("/upload-csv")
async def upload_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):

    # --------------------------------------------------------
    # 1. Vérification du fichier
    # --------------------------------------------------------

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Aucun fichier n'a été sélectionné."
        )

    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Le fichier doit être au format CSV."
        )

    try:

        # ----------------------------------------------------
        # 2. Lecture du fichier
        # ----------------------------------------------------

        contents = await file.read()

        if not contents:
            raise HTTPException(
                status_code=400,
                detail="Le fichier CSV est vide."
            )

        # utf-8-sig permet de gérer les CSV provenant d'Excel
        text = contents.decode("utf-8-sig")


        # ----------------------------------------------------
        # 3. Lecture du CSV
        #
        # sep=None permet de détecter automatiquement
        # la virgule "," ou le point-virgule ";"
        # ----------------------------------------------------

        df = pd.read_csv(
            io.StringIO(text),
            sep=None,
            engine="python"
        )


        # ----------------------------------------------------
        # 4. Nettoyage des noms de colonnes
        # ----------------------------------------------------

        df.columns = (
            df.columns
            .astype(str)
            .str.strip()
        )


        # ----------------------------------------------------
        # 5. Colonnes obligatoires
        # ----------------------------------------------------

        required_columns = [
            "date",
            "ice_fournisseur",
            "montant_ht",
            "taux_tva",
            "type_transaction"
        ]

        missing_columns = [
            column
            for column in required_columns
            if column not in df.columns
        ]

        if missing_columns:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Colonnes manquantes dans le CSV.",
                    "colonnes_attendues": required_columns,
                    "colonnes_trouvees": df.columns.tolist(),
                    "colonnes_manquantes": missing_columns
                }
            )


        # ----------------------------------------------------
        # 6. Vérification des lignes
        # ----------------------------------------------------

        if df.empty:
            raise HTTPException(
                status_code=400,
                detail="Le fichier CSV ne contient aucune facture."
            )


        # ----------------------------------------------------
        # 7. Conversion du montant HT
        # ----------------------------------------------------

        df["montant_ht"] = pd.to_numeric(
            df["montant_ht"]
            .astype(str)
            .str.strip()
            .str.replace(",", ".", regex=False),
            errors="coerce"
        )

        if df["montant_ht"].isna().any():

            lignes_invalides = (
                df.index[df["montant_ht"].isna()]
                .tolist()
            )

            raise HTTPException(
                status_code=400,
                detail=(
                    "Le montant_ht contient des valeurs invalides. "
                    f"Lignes concernées : {lignes_invalides}"
                )
            )


        # ----------------------------------------------------
        # 8. Conversion du taux TVA
        # ----------------------------------------------------

        df["taux_tva"] = pd.to_numeric(
            df["taux_tva"]
            .astype(str)
            .str.strip()
            .str.replace("%", "", regex=False)
            .str.replace(",", ".", regex=False),
            errors="coerce"
        )

        if df["taux_tva"].isna().any():

            lignes_invalides = (
                df.index[df["taux_tva"].isna()]
                .tolist()
            )

            raise HTTPException(
                status_code=400,
                detail=(
                    "Le taux_tva contient des valeurs invalides. "
                    f"Lignes concernées : {lignes_invalides}"
                )
            )


        # ----------------------------------------------------
        # 9. Conversion :
        #
        # 20   -> 0.20
        # 20%  -> 0.20
        # 0.20 -> 0.20
        # ----------------------------------------------------

        df.loc[
            df["taux_tva"] > 1,
            "taux_tva"
        ] = (
            df.loc[
                df["taux_tva"] > 1,
                "taux_tva"
            ] / 100
        )


        # ----------------------------------------------------
        # 10. Vérification du taux TVA
        # ----------------------------------------------------

        if (
            (df["taux_tva"] < 0)
            | (df["taux_tva"] > 1)
        ).any():

            raise HTTPException(
                status_code=400,
                detail=(
                    "Le taux de TVA doit être compris entre 0 et 1. "
                    "Exemples valides : 0.20, 0.10 ou 20%."
                )
            )


        # ----------------------------------------------------
        # 11. Conversion des dates
        # ----------------------------------------------------

        df["date"] = pd.to_datetime(
            df["date"],
            errors="coerce"
        )

        if df["date"].isna().any():

            lignes_invalides = (
                df.index[df["date"].isna()]
                .tolist()
            )

            raise HTTPException(
                status_code=400,
                detail=(
                    "Certaines dates sont invalides. "
                    f"Lignes concernées : {lignes_invalides}. "
                    "Exemple attendu : 2026-01-15."
                )
            )


        # ----------------------------------------------------
        # 12. Nettoyage du type de transaction
        # ----------------------------------------------------

        df["type_transaction"] = (
            df["type_transaction"]
            .astype(str)
            .str.strip()
            .str.upper()
        )


        # ----------------------------------------------------
        # 13. Vérification VENTE / ACHAT
        # ----------------------------------------------------

        types_valides = {
            "VENTE",
            "ACHAT"
        }

        types_invalides = (
            set(df["type_transaction"].unique())
            - types_valides
        )

        if types_invalides:

            raise HTTPException(
                status_code=400,
                detail=(
                    "Type de transaction invalide : "
                    f"{list(types_invalides)}. "
                    "Les valeurs autorisées sont VENTE et ACHAT."
                )
            )


        # ----------------------------------------------------
        # 14. Conversion en dictionnaires
        # ----------------------------------------------------

        factures_json = df.to_dict(
            orient="records"
        )


        # ----------------------------------------------------
        # 15. Préparation des factures
        # ----------------------------------------------------

        factures_stockees = []

        for item in factures_json:

            # Date
            date_obj = item["date"].date()

            # Montant HT
            montant_ht = float(
                item["montant_ht"]
            )

            # Taux TVA
            taux_tva = float(
                item["taux_tva"]
            )

            # Type transaction
            type_transaction = (
                str(item["type_transaction"])
                .strip()
                .upper()
            )


            # ------------------------------------------------
            # Calcul TVA
            # ------------------------------------------------

            resultats = calculer_tva_facture(
                montant_ht,
                taux_tva
            )


            # ------------------------------------------------
            # Création objet SQLAlchemy
            # ------------------------------------------------

            nouvelle_facture = InvoiceModel(

                date=date_obj,

                ice_fournisseur=str(
                    item["ice_fournisseur"]
                ),

                montant_ht=montant_ht,

                taux_tva=taux_tva,

                type_transaction=type_transaction,

                montant_tva=resultats[
                    "montant_tva"
                ],

                montant_ttc=resultats[
                    "montant_ttc"
                ]
            )


            db.add(nouvelle_facture)


            # ------------------------------------------------
            # Données utilisées pour le bilan
            # ------------------------------------------------

            factures_stockees.append({

                "date": date_obj,

                "ice_fournisseur": str(
                    item["ice_fournisseur"]
                ),

                "montant_ht": montant_ht,

                "taux_tva": taux_tva,

                "type_transaction": type_transaction
            })


        # ----------------------------------------------------
        # 16. Sauvegarde PostgreSQL
        # ----------------------------------------------------

        db.commit()


        # ----------------------------------------------------
        # 17. Calcul du bilan TVA
        # ----------------------------------------------------

        bilan_tva = faire_bilan_tva(
            factures_stockees
        )


        # ----------------------------------------------------
        # 18. Réponse
        # ----------------------------------------------------

        return {

            "status": "succès",

            "message": (
                f"{len(factures_stockees)} "
                "factures importées et sauvegardées."
            ),

            "bilan_fiscal": bilan_tva
        }


    # ========================================================
    # Erreur HTTP volontaire
    # ========================================================

    except HTTPException:

        db.rollback()

        # On conserve le vrai code 400
        raise


    # ========================================================
    # Erreur serveur
    # ========================================================

    except Exception as e:

        db.rollback()

        print("========================================")
        print("ERREUR IMPORT CSV")
        print("========================================")
        print(repr(e))
        print("========================================")

        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors du traitement : {str(e)}"
        )
# ============================================================
# VALIDER UNE DÉCLARATION MENSUELLE
# ============================================================

@app.post("/valider-declaration")
async def valider_declaration(
    mois: int,
    annee: int,
    db: Session = Depends(get_db)
):
    # 1. Récupérer toutes les factures VENTE et ACHAT pour ce mois/année
    factures_mois = db.query(InvoiceModel).filter(
        extract('year', InvoiceModel.date) == annee,
        extract('month', InvoiceModel.date) == mois
    ).all()

    if not factures_mois:
        raise HTTPException(status_code=404, detail="Aucune facture trouvée pour ce mois.")

    # 2. Convertir les objets SQLAlchemy en dictionnaires pour notre moteur de calcul
    factures_json = []
    for f in factures_mois:
        factures_json.append({
            "date": f.date,
            "ice_fournisseur": f.ice_fournisseur,
            "montant_ht": f.montant_ht,
            "taux_tva": f.taux_tva,
            "type_transaction": f.type_transaction
        })

    # 3. Calculer le bilan via notre moteur existant
    bilan = faire_bilan_tva(factures_json)

    # 4. Vérifier si une déclaration existe déjà pour ce mois
    declaration_existante = db.query(DeclarationModel).filter(
        DeclarationModel.mois == mois,
        DeclarationModel.annee == annee
    ).first()

    if declaration_existante:
        # Si elle existe, on met à jour les montants
        declaration_existante.total_ht_ventes = bilan["total_ht_ventes"]
        declaration_existante.total_tva_collectee = bilan["total_tva_collectee"]
        declaration_existante.total_ht_achats = bilan["total_ht_achats"]
        declaration_existante.total_tva_deductible = bilan["total_tva_deductible"]
        declaration_existante.tva_nette_a_payer = bilan["tva_nette_a_payer"]
        declaration_existante.date_creation = datetime.now()
    else:
        # 5. Créer une nouvelle déclaration
        nouvelle_declaration = DeclarationModel(
            company_ice="ICE_DEFAULT", # À remplacer plus tard par l'ICE de l'utilisateur
            mois=mois,
            annee=annee,
            total_ht_ventes=bilan["total_ht_ventes"],
            total_tva_collectee=bilan["total_tva_collectee"],
            total_ht_achats=bilan["total_ht_achats"],
            total_tva_deductible=bilan["total_tva_deductible"],
            tva_nette_a_payer=bilan["tva_nette_a_payer"],
            statut="Validée"
        )
        db.add(nouvelle_declaration)

    db.commit()

    # 6. (Simulation du système de notification)
    # Dans une vraie version, ici on enverrait un Email / SMS via Twilio ou SendGrid
    print(f"🔔 ALERTE : Déclaration du mois {mois}/{annee} enregistrée. Montant à payer : {bilan['tva_nette_a_payer']} MAD.")
    print(f"📅 Échéance de paiement : 20/{mois+1}/{annee}")

    return {
        "message": f"Déclaration du {mois}/{annee} validée avec succès.",
        "bilan": bilan,
        "echeance_paiement": f"20/{mois+1}/{annee}"
    }

# ============================================================
# (NOUVEAU) RÉCUPÉRER L'HISTORIQUE DES DÉCLARATIONS
# ============================================================

@app.get("/declarations")
async def get_declarations(db: Session = Depends(get_db)):
    """
    Récupère toutes les déclarations validées pour les afficher dans le frontend.
    """
    declarations = db.query(DeclarationModel).order_by(
        DeclarationModel.annee.desc(), 
        DeclarationModel.mois.desc()
    ).all()
    
    # Conversion en format JSON pour le frontend
    resultats = []
    for dec in declarations:
        # Calcul de la date d'échéance (20 du mois suivant)
        if dec.mois == 12:
            mois_echeance = 1
            annee_echeance = dec.annee + 1
        else:
            mois_echeance = dec.mois + 1
            annee_echeance = dec.annee
        
        date_echeance = datetime(annee_echeance, mois_echeance, 20).date()
        date_echeance_str = date_echeance.strftime("%d/%m/%Y")
        
        # Calcul de l'état (En attente, Payée, En retard)
        aujourd_hui = datetime.now().date()
        etat = "En attente"
        if dec.statut == "Payée":
            etat = "Payée"
        elif aujourd_hui > date_echeance:
            etat = "⚠️ En retard"

        resultats.append({
            "id": dec.id,
            "mois": dec.mois,
            "annee": dec.annee,
            "total_ht_ventes": dec.total_ht_ventes,
            "total_tva_collectee": dec.total_tva_collectee,
            "total_ht_achats": dec.total_ht_achats,
            "total_tva_deductible": dec.total_tva_deductible,
            "tva_nette_a_payer": dec.tva_nette_a_payer,
            "date_creation": dec.date_creation.strftime("%d/%m/%Y"),
            "echeance": date_echeance_str,
            "etat": etat
        })
    
    return resultats

# ============================================================
# (NOUVEAU) TÉLÉCHARGER LE PDF D'UNE DÉCLARATION
# ============================================================

@app.get("/declarations/{declaration_id}/pdf")
async def telecharger_pdf_declaration(
    declaration_id: int,
    db: Session = Depends(get_db)
):
    # 1. Récupérer la déclaration dans la base
    declaration = db.query(DeclarationModel).filter(DeclarationModel.id == declaration_id).first()
    if not declaration:
        raise HTTPException(status_code=404, detail="Déclaration introuvable.")
    
    # 2. Préparer les données pour le PDF
    data = {
        "company_ice": declaration.company_ice,
        "mois": declaration.mois,
        "annee": declaration.annee,
        "total_ht_ventes": declaration.total_ht_ventes,
        "total_tva_collectee": declaration.total_tva_collectee,
        "total_ht_achats": declaration.total_ht_achats,
        "total_tva_deductible": declaration.total_tva_deductible,
        "tva_nette_a_payer": declaration.tva_nette_a_payer,
        "date_creation": declaration.date_creation.strftime("%d/%m/%Y")
    }
    
    # 3. Générer le fichier PDF (CORRECTION POUR WINDOWS)
    filename = f"declaration_{declaration.mois:02d}_{declaration.annee}.pdf"
    
    # On utilise le dossier courant du projet (où se trouve main.py)
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    filepath = os.path.join(current_dir, filename) 
    # Exemple de chemin final : C:\projects\projet_dgi_ia\declaration_01_2026.pdf
    
    generer_declaration_pdf(data, filepath)
    
    # 4. Retourner le fichier pour téléchargement
    return FileResponse(
        path=filepath,
        media_type="application/pdf",
        filename=filename
    )