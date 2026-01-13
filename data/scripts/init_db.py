# data/scripts/init_db.py

import sys
import os
from pathlib import Path

# === Ajouter le dossier backend au PYTHONPATH ===
BASE_DIR = Path(__file__).resolve().parents[2]   # dossier linguee_like
BACKEND_DIR = BASE_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))

# === Imports après avoir modifié le PYTHONPATH ===
from app.db.database import engine
from app.db.models import Base


def init_db():
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("Done.")


if __name__ == "__main__":
    init_db()