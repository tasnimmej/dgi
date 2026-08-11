from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.services.ocr import ocr_extract
from app import models
from app.auth import get_current_user

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/upload-invoice")
async def upload_invoice(file: UploadFile = File(...), db: Session = Depends(get_db), current_user: models.UserModel = Depends(get_current_user)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Aucun fichier n'a été sélectionné.")

    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Fichier vide.")

    # Support images for now (png/jpg) - PDF not yet supported
    try:
        data = ocr_extract(contents)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur OCR: {e}")

    # Basic validation
    if 'montant_ht' not in data or data.get('montant_ht') is None:
        # still store raw text for manual extraction
        invoice = models.InvoiceModel(
            date=None,
            ice_fournisseur=(data.get('ice') or ''),
            montant_ht=0.0,
            taux_tva=(data.get('taux_tva') or 0.0),
            type_transaction='VENTE',
            company_id=current_user.company_id,
            montant_tva=0.0,
            montant_ttc=0.0
        )
        db.add(invoice)
        db.commit()
        db.refresh(invoice)
        return {"message": "Facture enregistrée (données incomplètes, vérifier manuellement)", "ocr": data}

    # Create invoice record using OCR values
    invoice = models.InvoiceModel(
        date=None,
        ice_fournisseur=(data.get('ice') or ''),
        montant_ht=float(data.get('montant_ht') or 0.0),
        taux_tva=float(data.get('taux_tva') or 0.0),
        type_transaction='VENTE',
        company_id=current_user.company_id,
        montant_tva=(float(data.get('montant_ht')) * float(data.get('taux_tva') or 0.0) if data.get('taux_tva') else 0.0),
        montant_ttc=(float(data.get('total_ttc')) if data.get('total_ttc') else 0.0)
    )

    db.add(invoice)
    db.commit()
    db.refresh(invoice)

    return {"message": "Facture OCR enregistrée", "invoice_id": invoice.id, "ocr": data}
