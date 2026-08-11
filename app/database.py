from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# URL de connexion à votre base PostgreSQL (admin:admin@localhost:5432/dgi_db)
SQLALCHEMY_DATABASE_URL = "postgresql://admin:admin@localhost:5432/dgi_db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()