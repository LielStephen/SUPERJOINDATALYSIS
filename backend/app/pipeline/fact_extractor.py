import re
import uuid
import multiprocessing
from typing import List, Dict, Any, Optional
import spacy
from backend.app.pipeline.pdf_parser import PDFPageData
from backend.app.pipeline.normalizer import FactNormalizer

try:
    nlp = spacy.load("en_core_web_sm", disable=["lemmatizer", "textcat"])
except Exception:
    try:
        import spacy.cli
        spacy.cli.download("en_core_web_sm")
        nlp = spacy.load("en_core_web_sm", disable=["lemmatizer", "textcat"])
    except Exception:
        nlp = spacy.blank("en")


class ExtractedFactItem:
    __slots__ = ['id', 'subject', 'predicate', 'raw_value', 'fact_type', 'source_text', 'page_number', 'bounding_box', 'confidence']

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

    # PRE-COMPILE REGEX FOR MASSIVE SPEEDUP IN TIGHT LOOPS
    PATTERNS = [
        {
            "category": "Operating Margin",
            "regex": re.compile(r'(?P<qualifier>GAAP|Non-GAAP|Adjusted Non-GAAP)?\s*Operating\s+Margin[A-Za-z0-9\s,]+?\s+(?P<value>[\d.]+%)', re.IGNORECASE),
            "predicate": "operating margin",
            "type": "PERCENTAGE"
        },
        {
            "category": "Revenue",
            "regex": re.compile(r'(?P<subject>[A-Za-z0-9\s]+?)\s+(?:segment\s+)?(?:revenue\s+)?(?:reached|was|grew\s+to|crossed|generated)\s+(?P<value>[$€£₹]?\s*[\d.]+\s*(?:billion|million|B|M|thousand|k)?)\b', re.IGNORECASE),
            "predicate": "revenue",
            "type": "CURRENCY"
        },
        {
            "category": "Growth",
            "regex": re.compile(r'(?:representing|growing\s+by|expanded\s+by|expansion\s+of)\s+(?P<value>[\d.]+%)\s*(?P<qualifier>year-over-year|annual|YoY)?', re.IGNORECASE),
            "predicate": "annual growth",
            "type": "PERCENTAGE"
        },
        {
            "category": "Headcount",
            "regex": re.compile(r'(?:headcount|workforce|employees|company)\s+(?:[A-Za-z0-9,\s]+?\s+)?(?:stood\s+at|was|closed\s+(?:fiscal\s+year\s+\d+\s+)?with)\s+(?P<value>[\d,]+)\s+(?P<unit>full-time employees|active permanent employees|employees)', re.IGNORECASE),
            "predicate": "headcount",
            "type": "NUMERICAL"
        },
        {
            "category": "Capital Expenditure",
            "regex": re.compile(r'accelerate\s+(?:capital\s+deployment|capex)\s+by\s+(?:an\s+additional\s+)?(?P<value>[\d.]%+)', re.IGNORECASE),
            "predicate": "capital deployment growth",
            "type": "PERCENTAGE"
        }
    ]

    # FAST SUBSTRING MATCHING SET
    CURRENCY_INDICATORS = {"$", "€", "£", "₹", "USD", "EUR", "billion", "million"}
    SKIP_PREDICATES = {"quarter", "year", "results", "figure", "table", "december"}

    @classmethod
    def extract_facts_from_pages(cls, doc_id: str, filename: str, pages: List[PDFPageData]) -> List[Dict[str, Any]]:
        extracted_facts: List[Dict[str, Any]] = []

        page_texts = [page.text for page in pages]
        
        # Heavy duty parallel processing utilizing available cores
        n_cores = max(1, multiprocessing.cpu_count() - 1)
        docs = list(nlp.pipe(page_texts, batch_size=50, n_process=n_cores))

        for page_idx, doc in enumerate(docs):
            page = pages[page_idx]
            page_blocks = page.blocks 

            for sent in doc.sents:
                sent_text = sent.text.strip()
                if len(sent_text) < 15:
                    continue

                # Short-circuit generator for faster bounding box lookup
                bbox = next((block["bbox"] for block in page_blocks if sent_text in block["text"] or block["text"] in sent_text), None)

                # Cache entities and chunks to avoid redundant spacy property evaluations
                ents = sent.ents

                matched_patterns = cls._apply_pattern_rules(ents, sent_text)
                if matched_patterns:
                    for item in matched_patterns:
                        extracted_facts.append(cls._build_fact_dict(
                            doc_id, filename, page.page_number, sent_text, page.text,
                            item["subject"], item["predicate"], item["raw_value"],
                            item["fact_type"], bbox, 0.95
                        ))
                else:
                    nlp_facts = cls._apply_nlp_extraction(sent, ents)
                    for item in nlp_facts:
                        extracted_facts.append(cls._build_fact_dict(
                            doc_id, filename, page.page_number, sent_text, page.text,
                            item["subject"], item["predicate"], item["raw_value"],
                            item["fact_type"], bbox, item["confidence"]
                        ))

        return extracted_facts

    @classmethod
    def _apply_pattern_rules(cls, ents, sent_text: str) -> List[Dict[str, Any]]:
        results = []
        for pat in cls.PATTERNS:
            match = pat["regex"].search(sent_text)
            if match:
                groups = match.groupdict()
                raw_val = groups.get("value", "")
                subject = groups.get("subject", "").strip()

                if not subject or len(subject) < 2 or "company" in subject.lower():
                    # Fast generator fallback
                    orgs = next((ent.text for ent in ents if ent.label_ in ("ORG", "PRODUCT")), None)
                    subject = orgs if orgs else "Company / Entity"

                pred = pat["predicate"]
                qual = groups.get("qualifier")
                if qual:
                    pred = f"{qual} {pred}"

                results.append({
                    "subject": subject,
                    "predicate": pred,
                    "raw_value": raw_val,
                    "fact_type": pat["type"]
                })
        return results

    @classmethod
    def _apply_nlp_extraction(cls, sent_spacy, ents) -> List[Dict[str, Any]]:
        num_ents, org_ents = [], []
        
        # Single pass entity categorization
        for e in ents:
            lbl = e.label_
            if lbl in ("MONEY", "PERCENT", "QUANTITY", "CARDINAL"):
                num_ents.append(e)
            elif lbl in ("ORG", "GPE", "PERSON"):
                org_ents.append(e)

        if not num_ents:
            return []

        results = []
        default_subj = org_ents[0].text if org_ents else "Corporate Entity"
        noun_chunks = list(sent_spacy.noun_chunks)

        for val_ent in num_ents:
            raw_val = val_ent.text.strip()
            # Fast rejection logic
            if (len(raw_val) == 4 and raw_val.startswith(("19", "20"))) or (len(raw_val) < 2 and not raw_val.isdigit()):
                continue

            pred = "reported metric"
            found_pred = False
            
            for chunk in noun_chunks:
                if val_ent.start >= chunk.start and val_ent.end <= chunk.end:
                    # String replace is much faster than re.sub + re.escape here
                    clean_chunk = chunk.text.replace(val_ent.text, '').strip()
                    if len(clean_chunk) > 2:
                        pred = clean_chunk
                        found_pred = True
                        break
                elif chunk.end <= val_ent.start:
                    pred = chunk.text
                    found_pred = True

            if not found_pred:
                for token in sent_spacy:
                    if token.pos_ == "NOUN" and token.dep_ in ("ROOT", "dobj", "pobj", "attr"):
                        lower_txt = token.text.lower()
                        if lower_txt not in cls.SKIP_PREDICATES:
                            pred = lower_txt
                            break

            lbl = val_ent.label_
            fact_type = "NUMERICAL"
            if lbl == "MONEY" or any(c in raw_val for c in cls.CURRENCY_INDICATORS):
                fact_type = "CURRENCY"
            elif lbl == "PERCENT" or "%" in raw_val or "percent" in raw_val.lower():
                fact_type = "PERCENTAGE"

            results.append({
                "subject": default_subj,
                "predicate": pred.strip(),
                "raw_value": raw_val,
                "fact_type": fact_type,
                "confidence": 0.88
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
        # Generate single UUID to slice from (halves UUID generation overhead)
        hex_str = uuid.uuid4().hex
        fact_id = f"F-{hex_str[:6].upper()}"
        ev_id = f"EV-{hex_str[6:12].upper()}"

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
                "id": ev_id,
                "fact_id": fact_id,
                "document_id": doc_id,
                "filename": filename,
                "page_number": page_number,
                "source_text": source_text,
                "bounding_box": bbox
            }
        }
