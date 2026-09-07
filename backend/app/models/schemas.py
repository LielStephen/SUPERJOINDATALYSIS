from datetime import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, ConfigDict

class FactEvidenceSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[str] = None
    fact_id: Optional[str] = None
    document_id: str
    filename: str
    page_number: int
    source_text: str
    bounding_box: Optional[List[float]] = None

class FactSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    document_id: str
    subject: str
    predicate: str
    raw_value: str
    fact_type: str
    normalized_value: Optional[float] = None
    normalized_str: Optional[str] = None
    unit: Optional[str] = None
    currency: Optional[str] = None
    temporal_type: Optional[str] = None
    temporal_year: Optional[int] = None
    temporal_quarter: Optional[int] = None
    temporal_period: Optional[str] = None
    scope_qualifiers: Optional[List[str]] = None
    confidence: float = 1.0
    entity_id: Optional[str] = None
    evidence: Optional[FactEvidenceSchema] = None

class DocumentSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    filename: str
    page_count: int
    processing_status: str
    upload_date: datetime
    fact_count: int

class DocumentDetailSchema(DocumentSchema):
    pages: List[Dict[str, Any]] = []

class RelationshipSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    category: str  # CORROBORATES, CONTRADICTS, CONTEXTUALIZES, TEMPORAL_CHANGE, PARTIALLY_SUPPORTS, UNCERTAIN
    fact_id_a: str
    fact_id_b: str
    fact_a: Optional[FactSchema] = None
    fact_b: Optional[FactSchema] = None
    confidence: float
    reasoning: str
    diagnostic_fix: Optional[str] = None
    context_diffs: Optional[Dict[str, Any]] = None

class EntitySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    canonical_name: str
    entity_type: str
    aliases: List[str] = []
