import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import JWTError, jwt

from app import models
from app.database import SessionLocal
from app.schemas import UserCreate, UserOut, Token, UserLogin, TokenData, CompanyCreate, CompanyOut

# --- Configuration sécurité ---
SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-super-secret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 jours

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


@router.post("/register", response_model=UserOut)
def register(user: UserCreate, db: Session = Depends(get_db)):
    # Vérifier si email existe
    existing = db.query(models.UserModel).filter(models.UserModel.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Un utilisateur avec cet email existe déjà.")

    # Si company_ice fourni, chercher la société
    company = None
    if user.company_ice:
        company = db.query(models.CompanyModel).filter(models.CompanyModel.ice == user.company_ice).first()

    # Sinon créer une société minimale si company_name présent
    if not company:
        if user.company_ice or user.company_name:
            company = models.CompanyModel(
                ice=(user.company_ice or f"ICE-{user.email}"),
                name=(user.company_name or "Société non renseignée")
            )
            db.add(company)
            db.commit()
            db.refresh(company)

    hashed = get_password_hash(user.password)
    role = "comptable"

    db_user = models.UserModel(
        email=user.email,
        hashed_password=hashed,
        full_name=user.full_name,
        role=role,
        company_id=(company.id if company else None)
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


@router.post("/login", response_model=Token)
def login(form_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.UserModel).filter(models.UserModel.email == form_data.email).first()
    if not user:
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")

    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")

    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


# Dépendance pour récupérer l'utilisateur courant
from fastapi import Header
from typing import Optional

def get_current_user(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)):
    """
    Lit l'en-tête Authorization: "Bearer <token>" et retourne l'utilisateur.
    """
    if authorization is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token manquant")

    # authorization attendu: "Bearer <token>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="En-tête Authorization invalide")

    token = parts[1]

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Token invalide")
        token_data = TokenData(email=email)
    except JWTError:
        raise HTTPException(status_code=401, detail="Token invalide")

    user = db.query(models.UserModel).filter(models.UserModel.email == token_data.email).first()
    if user is None:
        raise HTTPException(status_code=401, detail="Utilisateur introuvable")
    return user


@router.get("/me", response_model=UserOut)
def read_me(current_user: models.UserModel = Depends(get_current_user)):
    return current_user
