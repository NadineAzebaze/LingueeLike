# backend/app/nlp/indexer.py

from collections import defaultdict
from sqlalchemy.orm import Session
from app.db.models import WordTranslation, StemForm, Alignment, Segment
from app.nlp.stemmer import tokenize_and_stem


def build_word_index(db: Session):
    """
    Build co-occurrence word translation index from all aligned sentence pairs.
    Uses Dice coefficient: Dice(x,y) = 2 * co(x,y) / (count(x) + count(y))
    """
    alignments = db.query(Alignment).all()

    co_occur = defaultdict(int)
    en_word_count = defaultdict(int)
    fr_word_count = defaultdict(int)
    stem_surfaces_en = defaultdict(set)
    stem_surfaces_fr = defaultdict(set)

    for align in alignments:
        seg_en = db.get(Segment, align.segment_en_id)
        seg_fr = db.get(Segment, align.segment_fr_id)
        if not seg_en or not seg_fr:
            continue

        en_tokens = tokenize_and_stem(seg_en.text, "en")
        fr_tokens = tokenize_and_stem(seg_fr.text, "fr")

        en_stems = set()
        fr_stems = set()

        for s, surface in en_tokens:
            en_stems.add(s)
            stem_surfaces_en[s].add(surface)

        for s, surface in fr_tokens:
            fr_stems.add(s)
            stem_surfaces_fr[s].add(surface)

        for es in en_stems:
            en_word_count[es] += 1
        for fs in fr_stems:
            fr_word_count[fs] += 1

        for es in en_stems:
            for fs in fr_stems:
                co_occur[(es, fs)] += 1

    # Compute Dice coefficient and filter
    MIN_DICE = 0.1
    entries = []

    for (es, fs), co_count in co_occur.items():
        dice = 2.0 * co_count / (en_word_count[es] + fr_word_count[fs])
        if dice >= MIN_DICE:
            entries.append({
                "source_stem": es, "source_lang": "en",
                "target_stem": fs, "target_lang": "fr",
                "score": round(dice, 4),
                "co_occurrence_count": co_count,
                "source_count": en_word_count[es],
                "target_count": fr_word_count[fs],
            })
            entries.append({
                "source_stem": fs, "source_lang": "fr",
                "target_stem": es, "target_lang": "en",
                "score": round(dice, 4),
                "co_occurrence_count": co_count,
                "source_count": fr_word_count[fs],
                "target_count": en_word_count[es],
            })

    # Clear and rebuild
    db.query(WordTranslation).delete()
    db.query(StemForm).delete()

    for entry in entries:
        db.add(WordTranslation(**entry))

    for s, surfaces in stem_surfaces_en.items():
        for surface in surfaces:
            db.add(StemForm(stem=s, surface_form=surface, language="en"))

    for s, surfaces in stem_surfaces_fr.items():
        for surface in surfaces:
            db.add(StemForm(stem=s, surface_form=surface, language="fr"))

    db.commit()
    return len(entries)
