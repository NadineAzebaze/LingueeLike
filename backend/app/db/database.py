from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# Chemin absolu vers backend/linguee_like.db
BASE_DIR = Path(__file__).resolve().parents[2]  # backend/
DB_PATH = BASE_DIR / "linguee_like.db"

# Si settings.DATABASE_URL est vide → on utilise le chemin absolu
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL or f"sqlite:///{DB_PATH.as_posix()}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in SQLALCHEMY_DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

from app.db import models

Base.metadata.create_all(bind=engine)