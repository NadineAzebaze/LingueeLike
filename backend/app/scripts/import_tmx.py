import xml.etree.ElementTree as ET
from sqlalchemy.orm import Session
from app.db.models import Book, Segment, Alignment

def import_tmx(filepath: str, db: Session):
    tree = ET.parse(filepath)
    root = tree.getroot()

    header = root.find("header")

    # Métadonnées du Book (fallback si absentes)
    book = Book(
        title=header.get("o-book-title", "Imported TMX"),
        author=header.get("o-book-author", "Unknown"),
        year=int(header.get("o-book-year", 0)) if header.get("o-book-year") else None,
        language=header.get("o-book-language", "en"),
        source="tmx"
    )
    db.add(book)
    db.commit()
    db.refresh(book)

    print(f"📘 Book créé : {book.title} (id={book.id})")

    body = root.find("body")
    position = 1

    for tu in body.findall("tu"):
        tuv_list = tu.findall("tuv")

        seg_en = None
        seg_fr = None

        for tuv in tuv_list:
            lang = tuv.get("{http://www.w3.org/XML/1998/namespace}lang")
            seg_text = tuv.find("seg").text.strip()

            if lang == "en":
                seg_en = Segment(
                    book_id=book.id,
                    position=position,
                    language="en",
                    text=seg_text
                )
                db.add(seg_en)

            elif lang == "fr":
                seg_fr = Segment(
                    book_id=book.id,
                    position=position,
                    language="fr",
                    text=seg_text
                )
                db.add(seg_fr)

        db.commit()

        # Créer l’alignement si les deux segments existent
        if seg_en and seg_fr:
            alignment = Alignment(
                segment_en_id=seg_en.id,
                segment_fr_id=seg_fr.id,
                confidence=1.0
            )
            db.add(alignment)
            db.commit()

            print(f"✔ Alignement : EN({seg_en.id}) ↔ FR({seg_fr.id})")

        position += 1

    print("🎉 Import TMX terminé.")