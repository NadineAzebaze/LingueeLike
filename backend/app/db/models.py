# backend/app/db/models.py
from sqlalchemy import Column, Integer, String, ForeignKey, Float, Text, Index, UniqueConstraint
from sqlalchemy.orm import relationship

from .database import Base


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    author = Column(String, nullable=True)
    year = Column(Integer, nullable=True)
    language = Column(String(2), index=True)  # 'fr' or 'en'
    source = Column(String, nullable=True)

    segments = relationship("Segment", back_populates="book")


class Segment(Base):
    __tablename__ = "segments"

    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"), index=True)
    position = Column(Integer, index=True)
    language = Column(String(2), index=True)  # 'fr' or 'en'
    text = Column(Text, nullable=False)

    book = relationship("Book", back_populates="segments")
    alignments_fr = relationship(
        "Alignment", foreign_keys="Alignment.segment_fr_id", back_populates="segment_fr"
    )
    alignments_en = relationship(
        "Alignment", foreign_keys="Alignment.segment_en_id", back_populates="segment_en"
    )


class Alignment(Base):
    __tablename__ = "alignments"

    id = Column(Integer, primary_key=True, index=True)
    segment_fr_id = Column(Integer, ForeignKey("segments.id"))
    segment_en_id = Column(Integer, ForeignKey("segments.id"))
    confidence = Column(Float, nullable=True)

    segment_fr = relationship("Segment", foreign_keys=[segment_fr_id], back_populates="alignments_fr")
    segment_en = relationship("Segment", foreign_keys=[segment_en_id], back_populates="alignments_en")


class WordTranslation(Base):
    __tablename__ = "word_translations"

    id = Column(Integer, primary_key=True, index=True)
    source_stem = Column(String, nullable=False)
    source_lang = Column(String(2), nullable=False)
    target_stem = Column(String, nullable=False)
    target_lang = Column(String(2), nullable=False)
    score = Column(Float, nullable=False)
    co_occurrence_count = Column(Integer, default=0)
    source_count = Column(Integer, default=0)
    target_count = Column(Integer, default=0)

    __table_args__ = (
        Index("ix_word_trans_lookup", "source_stem", "source_lang"),
        UniqueConstraint("source_stem", "source_lang", "target_stem", "target_lang", name="uq_word_pair"),
    )


class StemForm(Base):
    __tablename__ = "stem_forms"

    id = Column(Integer, primary_key=True, index=True)
    stem = Column(String, nullable=False)
    surface_form = Column(String, nullable=False)
    language = Column(String(2), nullable=False)

    __table_args__ = (
        UniqueConstraint("stem", "surface_form", "language", name="uq_stem_surface"),
        Index("ix_stem_lookup", "stem", "language"),
    )