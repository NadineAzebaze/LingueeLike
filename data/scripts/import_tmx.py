# data/scripts/import_tmx.py
import sys
from pathlib import Path
import xml.etree.ElementTree as ET

# === Ajouter backend au PYTHONPATH ===
BASE_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = BASE_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import func
from app.db.database import SessionLocal
from app.db.models import Book, Segment, Alignment

BATCH_SIZE = 500  # commit par lots pour les gros fichiers


def clean_text(s):
    if s is None:
        return None
    return s.strip()


def import_tmx(file_path: str):
    print(f"Importing TMX file: {file_path}")

    tree = ET.parse(file_path)
    root = tree.getroot()

    session = SessionLocal()

    try:
        # === 1. Créer deux livres : EN et FR ===
        book_en = Book(title="TMX Import EN", language="en", source=file_path)
        book_fr = Book(title="TMX Import FR", language="fr", source=file_path)

        session.add_all([book_en, book_fr])
        session.commit()  # commit pour obtenir book_en.id / book_fr.id

        position = 0
        count = 0

        # === 2. Parcourir les unités de traduction ===
        for tu in root.iter("tu"):
            source = None
            target = None

            for tuv in tu.iter("tuv"):
                # récupération de l'attribut xml:lang
                lang = tuv.attrib.get("{http://www.w3.org/XML/1998/namespace}lang")
                seg_elem = tuv.find("seg")
                seg = seg_elem.text if seg_elem is not None else None
                seg = clean_text(seg)

                if lang == "en":
                    source = seg
                elif lang == "fr":
                    target = seg

            # Si on a bien une paire EN ↔ FR
            if source and target:
                position += 1
                count += 1

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

                session.add_all([seg_en, seg_fr])
                session.flush()  # obtenir seg_en.id et seg_fr.id sans commit

                # Mettre à jour search_vector pour chaque segment (Postgres)
                # Utilise to_tsvector selon la langue
                dialect_name = session.bind.dialect.name  # 'sqlite', 'postgresql', etc.

                if dialect_name == "postgresql":
                    # Postgres : utiliser to_tsvector
                    session.execute(
                        Segment.__table__.update()
                        .where(Segment.id == seg_en.id)
                        .values(search_vector=func.to_tsvector("english", seg_en.text))
                    )
                    session.execute(
                        Segment.__table__.update()
                        .where(Segment.id == seg_fr.id)
                        .values(search_vector=func.to_tsvector("french", seg_fr.text))
                    )
                else:
                    # SQLite ou autre : stocker le texte brut (ou NULL si tu préfères)
                    session.execute(
                        Segment.__table__.update()
                        .where(Segment.id == seg_en.id)
                        .values(search_vector=seg_en.text)
                    )
                    session.execute(
                        Segment.__table__.update()
                        .where(Segment.id == seg_fr.id)
                        .values(search_vector=seg_fr.text)
                    )


                # === 4. Créer l’alignement ===
                alignment = Alignment(
                    segment_en_id=seg_en.id,
                    segment_fr_id=seg_fr.id,
                    confidence=1.0
                )
                session.add(alignment)

                # Commit par lots
                if count % BATCH_SIZE == 0:
                    session.commit()
                    print(f"Committed {count} pairs...")

        # commit final
        session.commit()
        print(f"Import completed. Total pairs imported: {count}")

    except Exception as e:
        session.rollback()
        print("Error during import:", e)
        raise
    finally:
        session.close()


if __name__ == "__main__":
    tmx_path = BASE_DIR / "data" / "tmx" / "test.tmx"
    import_tmx(str(tmx_path))