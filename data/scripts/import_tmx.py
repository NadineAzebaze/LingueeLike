import sys
import os
from pathlib import Path
import xml.etree.ElementTree as ET

# === Ajouter backend au PYTHONPATH ===
BASE_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = BASE_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.db.database import SessionLocal
from app.db.models import Book, Segment, Alignment


def import_tmx(file_path: str):
    print(f"Importing TMX file: {file_path}")

    tree = ET.parse(file_path)
    root = tree.getroot()

    session = SessionLocal()

    # === 1. Créer deux livres : EN et FR ===
    book_en = Book(title="TMX Import EN", language="en", source="tmx")
    book_fr = Book(title="TMX Import FR", language="fr", source="tmx")

    session.add(book_en)
    session.add(book_fr)
    session.commit()

    position = 0

    # === 2. Parcourir les unités de traduction ===
    for tu in root.iter("tu"):
        source = None
        target = None

        for tuv in tu.iter("tuv"):
            lang = tuv.attrib.get("{http://www.w3.org/XML/1998/namespace}lang")
            seg = tuv.find("seg").text if tuv.find("seg") is not None else None

            if lang == "en":
                source = seg
            elif lang == "fr":
                target = seg

        # Si on a bien une paire EN ↔ FR
        if source and target:
            position += 1

            # === 3. Créer les segments ===
            seg_en = Segment(
                book_id=book_en.id,
                position=position,
                language="en",
                text=source
            )

            seg_fr = Segment(
                book_id=book_fr.id,
                position=position,
                language="fr",
                text=target
            )

            session.add(seg_en)
            session.add(seg_fr)
            session.commit()

            # === 4. Créer l’alignement ===
            alignment = Alignment(
                segment_en_id=seg_en.id,
                segment_fr_id=seg_fr.id,
                confidence=1.0
            )

            session.add(alignment)

    session.commit()
    session.close()

    print("Import completed.")


if __name__ == "__main__":
    tmx_path = BASE_DIR / "data" / "tmx" / "test.tmx"
    import_tmx(str(tmx_path))