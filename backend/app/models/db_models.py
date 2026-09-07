import datetime
from sqlalchemy import Column, String, Integer, Float, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from backend.app.database import Base

class DocumentDB(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    page_count = Column(Integer, default=0)
    processing_status = Column(String, default="PENDING")  # PENDING, PROCESSING, COMPLETED, FAILED
    upload_date = Column(DateTime, default=datetime.datetime.utcnow)
    fact_count = Column(Integer, default=0)

    pages = relationship("DocumentPageDB", back_populates="document", cascade="all, delete-orphan")
    facts = relationship("FactDB", back_populates="document", cascade="all, delete-orphan")

class DocumentPageDB(Base):
    __tablename__ = "document_pages"

    id = Column(String, primary_key=True, index=True)
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    page_number = Column(Integer, nullable=False)
    text_content = Column(Text, nullable=False)
    blocks_json = Column(JSON, nullable=True)  # Store list of text blocks with bounding boxes

    document = relationship("DocumentDB", back_populates="pages")

class EntityDB(Base):
    __tablename__ = "entities"

    id = Column(String, primary_key=True, index=True)
    canonical_name = Column(String, nullable=False, index=True)
    entity_type = Column(String, nullable=False)  # ORG, PERSON, GPE, METRIC, etc.
    aliases_json = Column(JSON, nullable=True)

class FactDB(Base):
    __tablename__ = "facts"

    id = Column(String, primary_key=True, index=True)
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    subject = Column(String, nullable=False, index=True)
    predicate = Column(String, nullable=False, index=True)
    raw_value = Column(String, nullable=False)
    fact_type = Column(String, nullable=False)  # NUMERICAL, PERCENTAGE, CURRENCY, DATE, RELATIONSHIP, STATUS, GEOGRAPHIC
    
    # Normalized fields
    normalized_value = Column(Float, nullable=True)
    normalized_str = Column(String, nullable=True)
    unit = Column(String, nullable=True)
    currency = Column(String, nullable=True)
    
    # Temporal & Scope fields
    temporal_type = Column(String, nullable=True)  # EXACT_DATE, FISCAL_YEAR, QUARTER, RANGE, RELATIVE
    temporal_year = Column(Integer, nullable=True)
    temporal_quarter = Column(Integer, nullable=True)
    temporal_period = Column(String, nullable=True)  # e.g., "FY2023", "Q4 2023", "December 31, 2023"
    scope_qualifiers_json = Column(JSON, nullable=True)  # e.g. ["GAAP", "Non-GAAP", "Consolidated", "Subsidiary"]
    
    confidence = Column(Float, default=1.0)
    entity_id = Column(String, ForeignKey("entities.id"), nullable=True)

    document = relationship("DocumentDB", back_populates="facts")
    evidence = relationship("FactEvidenceDB", back_populates="fact", uselist=False, cascade="all, delete-orphan")

class FactEvidenceDB(Base):
    __tablename__ = "fact_evidence"

    id = Column(String, primary_key=True, index=True)
    fact_id = Column(String, ForeignKey("facts.id"), nullable=False)
    document_id = Column(String, nullable=False)
    filename = Column(String, nullable=False)
    page_number = Column(Integer, nullable=False)
    source_text = Column(Text, nullable=False)  # Verbatim quote
    bounding_box_json = Column(JSON, nullable=True)  # [x0, y0, x1, y1]

    fact = relationship("FactDB", back_populates="evidence")

class RelationshipDB(Base):
    __tablename__ = "relationships"

    id = Column(String, primary_key=True, index=True)
    category = Column(String, nullable=False, index=True)  # CORROBORATES, CONTRADICTS, CONTEXTUALIZES, TEMPORAL_CHANGE, PARTIALLY_SUPPORTS, UNCERTAIN
    fact_id_a = Column(String, ForeignKey("facts.id"), nullable=False)
    fact_id_b = Column(String, ForeignKey("facts.id"), nullable=False)
    confidence = Column(Float, default=0.9)
    reasoning = Column(Text, nullable=False)
    diagnostic_fix = Column(Text, nullable=True)  # For failure/audit cases
    context_diffs_json = Column(JSON, nullable=True)  # Breakdown of scope/time/accounting differences
