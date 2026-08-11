from pydantic import BaseModel, EmailStr, Field
from typing import Optional
import datetime

# --- User schemas ---
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None
    company_ice: Optional[str] = None
    company_name: Optional[str] = None

class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: Optional[str]
    role: str

    class Config:
        orm_mode = True

# --- Token schemas ---
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    email: Optional[str] = None

# --- Login ---
class UserLogin(BaseModel):
    email: EmailStr
    password: str

# --- Company ---
class CompanyCreate(BaseModel):
    ice: str
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None

class CompanyOut(BaseModel):
    id: int
    ice: str
    name: Optional[str]

    class Config:
        orm_mode = True
