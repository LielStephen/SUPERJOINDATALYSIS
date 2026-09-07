import re
import uuid
from typing import List, Dict, Any, Optional
import spacy
from backend.app.pipeline.pdf_parser import PDFPageData
from backend.app.pipeline.normalizer import FactNormalizer

try:
    nlp = spacy.load("en_core_web_sm")
except Exception:
    try:
        import spacy.cli
        spacy.cli.download("en_core_web_sm")
        nlp = spacy.load("en_core_web_sm")
    except Exception:
        nlp = spacy.blank("en")


class ExtractedFactItem:
    def __init__(
        self,
        subject: str,
        predicate: str,
        raw_value: str,
        fact_type: str,
        source_text: str,
        page_number: int,
        bounding_box: Optional[List[float]] = None,
        confidence: float = 0.95
    ):
        self.id = f"F-{uuid.uuid4().hex[:8].upper()}"
        self.subject = subject
        self.predicate = predicate
        self.raw_value = raw_value
        self.fact_type = fact_type
        self.source_text = source_text
        self.page_number = page_number
        self.bounding_box = bounding_box
        self.confidence = confidence

class FactExtractionEngine:
    """Hybrid local fact extraction engine using Document Structure, Patterns, and spaCy NLP."""

    PATTERNS = [
        # Operating Margin e.g. "GAAP Operating Margin for fiscal year 2023 contracted to 21.4%" / "Adjusted Non-GAAP Operating Margin for FY23 was 28.6%"
        {
            "category": "Operating Margin",
            "regex": r'(?P<qualifier>GAAP|Non-GAAP|Adjusted Non-GAAP)?\s*Operating\s+Margin[A-Za-z0-9\s,]+?\s+(?P<value>[\d.]+%)',
            "predicate": "operating margin",
            "type": "PERCENTAGE"
        },
        # Cloud revenue / segment revenue e.g. "Cloud Infrastructure segment revenue reached $4.2 billion" / "crossed $4.2B"
        {
            "category": "Revenue",
            "regex": r'(?P<subject>[A-Za-z0-9\s]+?)\s+(?:segment\s+)?(?:revenue\s+)?(?:reached|was|grew\s+to|crossed|generated)\s+(?P<value>[$€£₹]?\s*[\d.]+\s*(?:billion|million|B|M|thousand|k)?)\b',
            "predicate": "revenue",
            "type": "CURRENCY"
        },
        # Cloud / segment YoY growth e.g. "representing 32% year-over-year expansion" / "growing by 32% compared to prior year"
        {
            "category": "Growth",
            "regex": r'(?:representing|growing\s+by|expanded\s+by|expansion\s+of)\s+(?P<value>[\d.]+%)\s*(?P<qualifier>year-over-year|annual|YoY)?',
            "predicate": "annual growth",
            "type": "PERCENTAGE"
        },
        # Headcount / Workforce e.g. "headcount as of December 31, 2023 stood at 14,200 full-time employees" / "closed fiscal year 2023 with 15,800 active permanent employees"
        {
            "category": "Headcount",
            "regex": r'(?:headcount|workforce|employees|company)\s+(?:[A-Za-z0-9,\s]+?\s+)?(?:stood\s+at|was|closed\s+(?:fiscal\s+year\s+\d+\s+)?with)\s+(?P<value>[\d,]+)\s+(?P<unit>full-time employees|active permanent employees|employees)',
            "predicate": "headcount",
            "type": "NUMERICAL"
        },
        # Capital Deployment / Capex e.g. "accelerate capital deployment by an additional 40% in the coming cycle"
        {
            "category": "Capital Expenditure",
            "regex": r'accelerate\s+(?:capital\s+deployment|capex)\s+by\s+(?:an\s+additional\s+)?(?P<value>[\d.]%+)',
            "predicate": "capital deployment growth",
            "type": "PERCENTAGE"
        }
    ]

    @classmethod
    def extract_facts_from_pages(cls, doc_id: str, filename: str, pages: List[PDFPageData]) -> List[Dict[str, Any]]:
        extracted_facts: List[Dict[str, Any]] = []

        for page in pages:
            doc = nlp(page.text)
            
            for sent in doc.sents:
                sent_text = sent.text.strip()
                if len(sent_text) < 15:
                    continue

                bbox = None
                for block in page.blocks:
                    if sent_text in block["text"] or block["text"] in sent_text:
                        bbox = block["bbox"]
                        break

                matched_patterns = cls._apply_pattern_rules(sent_text)
                for item in matched_patterns:
                    fact_obj = cls._build_fact_dict(
                        doc_id=doc_id,
                        filename=filename,
                        page_number=page.page_number,
                        source_text=sent_text,
                        page_text=page.text,
                        subject=item["subject"],
                        predicate=item["predicate"],
                        raw_value=item["raw_value"],
                        fact_type=item["fact_type"],
                        bbox=bbox,
                        confidence=0.95
                    )
                    extracted_facts.append(fact_obj)

                if not matched_patterns:
                    nlp_facts = cls._apply_nlp_extraction(sent, sent_text)
                    for item in nlp_facts:
                        fact_obj = cls._build_fact_dict(
                            doc_id=doc_id,
                            filename=filename,
                            page_number=page.page_number,
                            source_text=sent_text,
                            page_text=page.text,
                            subject=item["subject"],
                            predicate=item["predicate"],
                            raw_value=item["raw_value"],
                            fact_type=item["fact_type"],
                            bbox=bbox,
                            confidence=item["confidence"]
                        )
                        extracted_facts.append(fact_obj)

        return extracted_facts

    @classmethod
    def _apply_pattern_rules(cls, sent_text: str) -> List[Dict[str, Any]]:
        results = []
        for pat in cls.PATTERNS:
            match = re.search(pat["regex"], sent_text, re.IGNORECASE)
            if match:
                groups = match.groupdict()
                raw_val = groups.get("value", "")
                
                subject = groups.get("subject", "").strip()
                if not subject or len(subject) < 2 or "company" in subject.lower():
                    doc = nlp(sent_text)
                    orgs = [ent.text for ent in doc.ents if ent.label_ in ["ORG", "PRODUCT"]]
                    subject = orgs[0] if orgs else "Company / Entity"

                pred = pat["predicate"]
                if groups.get("qualifier"):
                    pred = f"{groups['qualifier']} {pred}"

                results.append({
                    "subject": subject,
                    "predicate": pred,
                    "raw_value": raw_val,
                    "fact_type": pat["type"]
                })
        return results

    @classmethod
    def _apply_nlp_extraction(cls, sent_spacy, sent_text: str) -> List[Dict[str, Any]]:
        results = []
        ents = sent_spacy.ents
        
        num_ents = [e for e in ents if e.label_ in ["MONEY", "PERCENT", "QUANTITY", "CARDINAL"]]
        org_ents = [e for e in ents if e.label_ in ["ORG", "GPE", "PERSON"]]

        if num_ents:
            val_ent = num_ents[0]
            subj = org_ents[0].text if org_ents else "Corporate Entity"
            
            pred = "reported metric"
            if "operating margin" in sent_text.lower() or "margin" in sent_text.lower():
                pred = "operating margin"
            else:
                for token in sent_spacy:
                    if token.pos_ in ["VERB", "NOUN"] and token.dep_ in ["ROOT", "dobj", "nsubj"]:
                        if token.text.lower() not in ["was", "is", "were", "are", "reached", "stood"]:
                            pred = token.text.lower()
                            break

            fact_type = "NUMERICAL"
            if val_ent.label_ == "MONEY":
                fact_type = "CURRENCY"
            elif val_ent.label_ == "PERCENT":
                fact_type = "PERCENTAGE"

            results.append({
                "subject": subj,
                "predicate": pred,
                "raw_value": val_ent.text,
                "fact_type": fact_type,
                "confidence": 0.85
            })
            
        return results

    @classmethod
    def _build_fact_dict(
        cls,
        doc_id: str,
        filename: str,
        page_number: int,
        source_text: str,
        page_text: str,
        subject: str,
        predicate: str,
        raw_value: str,
        fact_type: str,
        bbox: Optional[List[float]],
        confidence: float
    ) -> Dict[str, Any]:
        fact_id = f"F-{uuid.uuid4().hex[:6].upper()}"

        norm_res = FactNormalizer.normalize_number_and_unit(raw_value)
        temp_res = FactNormalizer.extract_temporal_context(source_text, page_text)
        scope_quals = FactNormalizer.extract_scope_qualifiers(source_text)

        return {
            "id": fact_id,
            "document_id": doc_id,
            "subject": subject.strip(),
            "predicate": predicate.strip(),
            "raw_value": raw_value,
            "fact_type": norm_res["fact_type"] or fact_type,
            "normalized_value": norm_res["normalized_value"],
            "normalized_str": norm_res["normalized_str"],
            "unit": norm_res["unit"],
            "currency": norm_res["currency"],
            "temporal_type": temp_res["temporal_type"],
            "temporal_year": temp_res["temporal_year"],
            "temporal_quarter": temp_res["temporal_quarter"],
            "temporal_period": temp_res["temporal_period"],
            "scope_qualifiers": scope_quals,
            "confidence": round(confidence, 2),
            "evidence": {
                "id": f"EV-{uuid.uuid4().hex[:6].upper()}",
                "fact_id": fact_id,
                "document_id": doc_id,
                "filename": filename,
                "page_number": page_number,
                "source_text": source_text,
                "bounding_box": bbox
            }
        }
