import os
import uuid
import datetime
from pathlib import Path
from typing import List, Optional
from fastapi import FastAPI, Depends, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.app.database import init_db, get_db
from backend.app.models.db_models import DocumentDB, DocumentPageDB, EntityDB, FactDB, FactEvidenceDB, RelationshipDB
from backend.app.models.schemas import DocumentSchema, DocumentDetailSchema, FactSchema, RelationshipSchema
from backend.app.pipeline.pdf_parser import PDFParser
from backend.app.pipeline.fact_extractor import FactExtractionEngine
from backend.app.pipeline.normalizer import FactNormalizer
from backend.app.pipeline.entity_resolution import EntityResolutionEngine
from backend.app.pipeline.candidate_matcher import CandidateFactMatcher
from backend.app.pipeline.relationship_engine import RelationshipEngine
from backend.app.sample_generator import generate_sample_pdfs, SAMPLE_DOCS_DIR

app = FastAPI(
    title="Fact Knowledge Layer API",
    description="Self-Contained Local Fact Extraction, Grounding, Normalization & Cross-Document Relationship Engine",
    version="2.0.0"
)

cors_origins_env = os.getenv("CORS_ORIGINS", "")
allowed_origins = [orig.strip() for orig in cors_origins_env.split(",") if orig.strip()] if cors_origins_env else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"^https://.*\.vercel\.app$|^http://localhost(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", str(Path(__file__).resolve().parent.parent.parent / "uploads")))
STATIC_DIR = Path(__file__).resolve().parent / "static"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/health")
@app.get("/healthz")
def health_check():
    return {"status": "healthy", "service": "Fact Knowledge Layer API"}

@app.get("/")
def read_root():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {
        "status": "online",
        "system": "Self-Contained Fact Knowledge Layer",
        "llm_dependency": "NONE (100% Local Pipeline)"
    }

# ---------------------------------------------------------
# Document Endpoints
# ---------------------------------------------------------

@app.post("/api/documents", response_model=DocumentSchema)
def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    init_db()
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    doc_id = f"DOC-{uuid.uuid4().hex[:8].upper()}"
    file_path = UPLOAD_DIR / f"{doc_id}_{file.filename}"
    
    with open(file_path, "wb") as f:
        f.write(file.file.read())

    try:
        page_count, _ = PDFParser.parse_pdf(str(file_path))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse PDF: {str(e)}")

    doc_db = DocumentDB(
        id=doc_id,
        filename=file.filename,
        file_path=str(file_path),
        page_count=page_count,
        processing_status="PENDING",
        upload_date=datetime.datetime.now(datetime.timezone.utc),
        fact_count=0
    )
    db.add(doc_db)
    db.commit()
    db.refresh(doc_db)
    return doc_db

@app.get("/api/documents", response_model=List[DocumentSchema])
def list_documents(db: Session = Depends(get_db)):
    init_db()
    return db.query(DocumentDB).order_by(DocumentDB.upload_date.desc()).all()

@app.get("/api/documents/{doc_id}", response_model=DocumentDetailSchema)
def get_document(doc_id: str, db: Session = Depends(get_db)):
    init_db()
    doc = db.query(DocumentDB).filter(DocumentDB.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    pages_data = []
    for p in doc.pages:
        pages_data.append({
            "page_number": p.page_number,
            "text_content": p.text_content,
            "blocks": p.blocks_json
        })

    return {
        "id": doc.id,
        "filename": doc.filename,
        "page_count": doc.page_count,
        "processing_status": doc.processing_status,
        "upload_date": doc.upload_date,
        "fact_count": doc.fact_count,
        "pages": pages_data
    }

@app.post("/api/documents/{doc_id}/process")
def process_document(doc_id: str, db: Session = Depends(get_db)):
    init_db()
    doc = db.query(DocumentDB).filter(DocumentDB.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    doc.processing_status = "PROCESSING"
    db.commit()

    try:
        page_count, pages_data = PDFParser.parse_pdf(doc.file_path)
        doc.page_count = page_count

        db.query(DocumentPageDB).filter(DocumentPageDB.document_id == doc_id).delete()
        for pdata in pages_data:
            db_page = DocumentPageDB(
                id=f"PG-{uuid.uuid4().hex[:8].upper()}",
                document_id=doc_id,
                page_number=pdata.page_number,
                text_content=pdata.text,
                blocks_json=pdata.blocks
            )
            db.add(db_page)

        extracted_facts = FactExtractionEngine.extract_facts_from_pages(
            doc_id=doc.id,
            filename=doc.filename,
            pages=pages_data
        )

        db.query(FactEvidenceDB).filter(FactEvidenceDB.document_id == doc_id).delete()
        db.query(FactDB).filter(FactDB.document_id == doc_id).delete()

        for fdict in extracted_facts:
            ev_data = fdict.pop("evidence")
            scope_q = fdict.pop("scope_qualifiers", [])
            fdict["scope_qualifiers_json"] = scope_q
            
            db_fact = FactDB(**fdict)
            db.add(db_fact)
            
            db_ev = FactEvidenceDB(
                id=ev_data["id"],
                fact_id=db_fact.id,
                document_id=ev_data["document_id"],
                filename=ev_data["filename"],
                page_number=ev_data["page_number"],
                source_text=ev_data["source_text"],
                bounding_box_json=ev_data["bounding_box"]
            )
            db.add(db_ev)

        doc.fact_count = len(extracted_facts)
        doc.processing_status = "COMPLETED"
        db.commit()

        reconcile_knowledge_layer(db)

        return {"status": "success", "extracted_facts": len(extracted_facts)}

    except Exception as e:
        doc.processing_status = "FAILED"
        db.commit()
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

# ---------------------------------------------------------
# Fact Endpoints
# ---------------------------------------------------------

@app.get("/api/facts", response_model=List[FactSchema])
def list_facts(doc_id: Optional[str] = None, fact_type: Optional[str] = None, db: Session = Depends(get_db)):
    init_db()
    query = db.query(FactDB)
    if doc_id:
        query = query.filter(FactDB.document_id == doc_id)
    if fact_type:
        query = query.filter(FactDB.fact_type == fact_type)
    facts_db = query.all()
    
    results = []
    for f in facts_db:
        f_schema = FactSchema.model_validate(f)
        f_schema.scope_qualifiers = f.scope_qualifiers_json or []
        results.append(f_schema)
    return results

@app.get("/api/facts/{fact_id}", response_model=FactSchema)
def get_fact(fact_id: str, db: Session = Depends(get_db)):
    init_db()
    fact = db.query(FactDB).filter(FactDB.id == fact_id).first()
    if not fact:
        raise HTTPException(status_code=404, detail="Fact not found.")
    f_schema = FactSchema.model_validate(fact)
    f_schema.scope_qualifiers = fact.scope_qualifiers_json or []
    return f_schema

# ---------------------------------------------------------
# Relationship Endpoints
# ---------------------------------------------------------

@app.get("/api/relationships", response_model=List[RelationshipSchema])
def list_relationships(category: Optional[str] = None, db: Session = Depends(get_db)):
    init_db()
    query = db.query(RelationshipDB)
    if category:
        query = query.filter(RelationshipDB.category == category)
    rel_list = query.all()
    
    results = []
    for r in rel_list:
        fa = db.query(FactDB).filter(FactDB.id == r.fact_id_a).first()
        fb = db.query(FactDB).filter(FactDB.id == r.fact_id_b).first()
        
        r_schema = RelationshipSchema.model_validate(r)
        r_schema.context_diffs = r.context_diffs_json
        
        if fa:
            fa_s = FactSchema.model_validate(fa)
            fa_s.scope_qualifiers = fa.scope_qualifiers_json or []
            r_schema.fact_a = fa_s
            
        if fb:
            fb_s = FactSchema.model_validate(fb)
            fb_s.scope_qualifiers = fb.scope_qualifiers_json or []
            r_schema.fact_b = fb_s
            
        results.append(r_schema)
        
    return results

@app.get("/api/relationships/{rel_id}", response_model=RelationshipSchema)
def get_relationship(rel_id: str, db: Session = Depends(get_db)):
    init_db()
    rel = db.query(RelationshipDB).filter(RelationshipDB.id == rel_id).first()
    if not rel:
        raise HTTPException(status_code=404, detail="Relationship not found.")
    
    fa = db.query(FactDB).filter(FactDB.id == rel.fact_id_a).first()
    fb = db.query(FactDB).filter(FactDB.id == rel.fact_id_b).first()
    
    r_schema = RelationshipSchema.model_validate(rel)
    r_schema.context_diffs = rel.context_diffs_json
    
    if fa:
        fa_s = FactSchema.model_validate(fa)
        fa_s.scope_qualifiers = fa.scope_qualifiers_json or []
        r_schema.fact_a = fa_s
        
    if fb:
        fb_s = FactSchema.model_validate(fb)
        fb_s.scope_qualifiers = fb.scope_qualifiers_json or []
        r_schema.fact_b = fb_s
        
    return r_schema

# ---------------------------------------------------------
# Seed & Demo Endpoint
# ---------------------------------------------------------

@app.post("/api/demo/seed")
def seed_demo_data(db: Session = Depends(get_db)):
    """Generates synthetic PDFs and processes them end-to-end to demonstrate the 4 challenge cases."""
    init_db()
    pdf_paths = generate_sample_pdfs()

    db.query(RelationshipDB).delete()
    db.query(FactEvidenceDB).delete()
    db.query(FactDB).delete()
    db.query(DocumentPageDB).delete()
    db.query(DocumentDB).delete()
    db.commit()

    processed_docs = []
    for pdf_path in pdf_paths:
        filename = pdf_path.name
        doc_id = f"DOC-{uuid.uuid4().hex[:6].upper()}"

        page_count, pages_data = PDFParser.parse_pdf(str(pdf_path))
        
        doc_db = DocumentDB(
            id=doc_id,
            filename=filename,
            file_path=str(pdf_path),
            page_count=page_count,
            processing_status="COMPLETED",
            upload_date=datetime.datetime.now(datetime.timezone.utc),
            fact_count=0
        )
        db.add(doc_db)
        db.commit()

        for pdata in pages_data:
            db_page = DocumentPageDB(
                id=f"PG-{uuid.uuid4().hex[:8].upper()}",
                document_id=doc_id,
                page_number=pdata.page_number,
                text_content=pdata.text,
                blocks_json=pdata.blocks
            )
            db.add(db_page)

        facts = FactExtractionEngine.extract_facts_from_pages(
            doc_id=doc_id,
            filename=filename,
            pages=pages_data
        )

        for fdict in facts:
            ev_data = fdict.pop("evidence")
            scope_q = fdict.pop("scope_qualifiers", [])
            fdict["scope_qualifiers_json"] = scope_q

            db_fact = FactDB(**fdict)
            db.add(db_fact)
            
            db_ev = FactEvidenceDB(
                id=ev_data["id"],
                fact_id=db_fact.id,
                document_id=ev_data["document_id"],
                filename=ev_data["filename"],
                page_number=ev_data["page_number"],
                source_text=ev_data["source_text"],
                bounding_box_json=ev_data["bounding_box"]
            )
            db.add(db_ev)

        doc_db.fact_count = len(facts)
        db.commit()
        processed_docs.append(doc_db.filename)

    reconcile_knowledge_layer(db)

    return {
        "status": "success",
        "message": f"Ingested and processed {len(processed_docs)} sample PDFs.",
        "documents": processed_docs
    }

# ---------------------------------------------------------
# Helper Pipeline Reconciler
# ---------------------------------------------------------

def reconcile_knowledge_layer(db: Session):
    """Executes global entity resolution, candidate matching, and relationship reasoning."""
    facts_db = db.query(FactDB).all()
    if not facts_db:
        return

    facts_dicts = []
    for f in facts_db:
        f_dict = {
            "id": f.id,
            "document_id": f.document_id,
            "subject": f.subject,
            "predicate": f.predicate,
            "raw_value": f.raw_value,
            "fact_type": f.fact_type,
            "normalized_value": f.normalized_value,
            "normalized_str": f.normalized_str,
            "unit": f.unit,
            "currency": f.currency,
            "temporal_type": f.temporal_type,
            "temporal_year": f.temporal_year,
            "temporal_quarter": f.temporal_quarter,
            "temporal_period": f.temporal_period,
            "scope_qualifiers": f.scope_qualifiers_json,
            "confidence": f.confidence,
            "entity_id": f.entity_id,
            "evidence": {
                "filename": f.evidence.filename if f.evidence else "",
                "page_number": f.evidence.page_number if f.evidence else 1,
                "source_text": f.evidence.source_text if f.evidence else ""
            }
        }
        facts_dicts.append(f_dict)

    subject_entity_map = EntityResolutionEngine.resolve_entities(facts_dicts)
    for f in facts_db:
        if f.subject in subject_entity_map:
            f.entity_id = subject_entity_map[f.subject]
    db.commit()

    for fd in facts_dicts:
        if fd["subject"] in subject_entity_map:
            fd["entity_id"] = subject_entity_map[fd["subject"]]

    candidate_pairs = CandidateFactMatcher.get_candidate_pairs(facts_dicts)

    db.query(RelationshipDB).delete()
    db.commit()

    for fact_a, fact_b in candidate_pairs:
        rel_result = RelationshipEngine.analyze_pair(fact_a, fact_b)
        
        db_rel = RelationshipDB(
            id=rel_result["id"],
            category=rel_result["category"],
            fact_id_a=rel_result["fact_id_a"],
            fact_id_b=rel_result["fact_id_b"],
            confidence=rel_result["confidence"],
            reasoning=rel_result["reasoning"],
            diagnostic_fix=rel_result["diagnostic_fix"],
            context_diffs_json=rel_result["context_diffs"]
        )
        db.add(db_rel)

    db.commit()
