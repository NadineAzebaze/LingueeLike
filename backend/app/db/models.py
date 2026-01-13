# backend/app/db/models.py
from sqlalchemy import Column, Integer, String, ForeignKey, Float
from sqlalchemy.orm import relationship
from .database import Base

class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    author = Column(String, nullable=True)
    year = Column(Integer, nullable=True)
    language = Column(String, index=True)  # 'fr' ou 'en'
    source = Column(String, nullable=True)

    segments = relationship("Segment", back_populates="book")

class Segment(Base):
    __tablename__ = "segments"

    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"))
    position = Column(Integer, index=True)
    language = Column(String, index=True)
    text = Column(String, index=True)

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