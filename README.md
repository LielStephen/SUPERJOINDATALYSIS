# Fact Knowledge Layer: Multi-Document Factual Reconciliation Engine

A 100% self-contained, evidence-grounded document intelligence system built with **Python**, **FastAPI**, **PyMuPDF**, **spaCy**, **SQLite**, and a **React workstation interface**.

> **CRITICAL ARCHITECTURAL DIRECTIVE**: This system performs all document analysis, page-aware text extraction, metric normalization, entity resolution, candidate matching, and relationship reasoning **100% locally within its own Python processing pipeline**. It **DOES NOT** upload PDFs or text to Gemini, OpenAI, Claude, or any third-party external LLM API.

---

## 1. System Architecture

```text
                        PDF Document
                             │
                             ▼
                    ┌──────────────────┐
                    │  PyMuPDF Parser  │ (Page-aware blocks & bounding boxes)
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ Fact Extraction  │
                    │      Engine      │
                    └────────┬─────────┘
                             │
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
   Document Structure   Pattern Rules      Local spaCy NLP
   (Sections, Headings) (Regex & Scales)   (NER & Dependencies)
        │                    │                    │
        └────────────────────┼────────────────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │  Normalization   │ (Numbers, Currency, %, Dates/Periods)
                    │      Engine      │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │Entity Resolution │ (Canonical clustering & Aliasing)
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │Candidate Matcher │ (Metric-bucket pair retrieval)
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │  Relationship    │ (Multi-dimensional decision tree)
                    │      Engine      │
                    └────────┬─────────┘
                             │
       ┌───────────┬─────────┴─────────┬───────────┐
       ▼           ▼                   ▼           ▼
 CORROBORATES CONTRADICTS       CONTEXTUALIZES UNCERTAIN
       │           │                   │           │
       └───────────┴─────────┬─────────┴───────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │  SQLite Database │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │   FastAPI REST   │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │React Workstation │
                    └──────────────────┘
```

---

## 2. Setup and Run Instructions

### Prerequisites
* Python 3.10 or higher
* Node.js v18+ (Optional, UI is served directly out-of-the-box by FastAPI)

### 1. Clone & Activate Virtual Environment
```bash
git clone https://github.com/LielStephen/SUPERJOINDATALYSIS.git
cd SUPERJOINDATALYSIS

# Create virtual environment
python -m venv .venv

# Activate on Windows (PowerShell)
.venv\Scripts\activate

# Activate on macOS / Linux
source .venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run Automated Tests
Verify all normalization, extraction, entity matching, and relationship logic:
```bash
python -m pytest backend/tests/test_pipeline.py -v
```

### 4. Launch Application
Start the FastAPI backend server (which serves the API and the React Workstation UI):
```bash
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

Open your browser at: **`http://localhost:8000`**

Click **"⚡ Seed Demo Dataset"** in the top navigation bar to generate synthetic PDF disclosures and run the full end-to-end extraction pipeline live.

---

## 3. Video Demo

* **Demo Video Link**: `https://youtu.be/your-demo-video-id` *(Replace with your 3-minute recording)*
* **Demo Highlights**:
  1. **Document Ingestion**: Uploading multi-page PDFs page-by-page preserving text block coordinates.
  2. **Local Extraction & Normalization**: Demonstrating zero external LLM usage with local spaCy NER, date parsing, and currency scales.
  3. **The 4 Challenge Cases**: Side-by-side evidence inspection of Corroboration, Contradiction, Contextual Difference, and Audit Failures.
  4. **Fact & Evidence Inspector**: Viewing verbatim source quotes and page bounding boxes.

---

## 4. Demonstration of the Four Required Cases

### Case 1: Corroborated Evidence
* **Claim**: Cloud Infrastructure segment revenue reached $4.2B with 32% year-over-year growth in Q4 2023.
* **Source Evidence**:
  * `Q4_2023_Earnings_Release.pdf` (Page 1): *"Cloud Infrastructure segment revenue reached $4.2 billion, representing 32% year-over-year expansion."*
  * `FY2023_Shareholder_Letter.pdf` (Page 1): *"Our cloud business crossed $4.2B in the fourth quarter, growing by 32% compared to the prior year period."*
* **System Reasoning**: Both documents independently confirm the identical fourth-quarter cloud financial performance ($4.2 billion revenue and 32% YoY growth rate). Entity resolution maps 'Cloud Infrastructure segment' and 'our cloud business' to the same entity cluster.

### Case 2: Genuine Contradiction
* **Claim**: Conflicting global workforce counts as of December 31, 2023.
* **Source Evidence**:
  * `Global_Workforce_Report_2023.pdf` (Page 1): *"Total global permanent headcount as of December 31, 2023 stood at 14,200 full-time employees."*
  * `Annual_ESG_Disclosure_2023.pdf` (Page 1): *"The company closed fiscal year 2023 with 15,800 active permanent employees worldwide."*
* **System Reasoning**: Direct numerical conflict between two official corporate disclosures for the exact same reporting cutoff date (December 31, 2023 / FY2023 end). One reports 14,200 full-time employees while the other states 15,800 active permanent employees (a 1,600 employee discrepancy) without accounting adjustments.

### Case 3: Contextual Reconciliation (Scope & Accounting Difference)
* **Claim**: Apparent variance in reported Operating Margin (21.4% vs. 28.6%).
* **Source Evidence**:
  * `Form_10K_Annual_Report.pdf` (Page 1): *"GAAP Operating Margin for fiscal year 2023 contracted to 21.4% reflecting acquisition-related restructuring charges."*
  * `Q4_Investor_Presentation.pdf` (Page 1): *"Adjusted Non-GAAP Operating Margin for FY23 was 28.6%, reflecting strong core software operational leverage."*
* **System Reasoning**: The 720 basis point difference between 21.4% and 28.6% is fully reconciled by textual accounting qualifiers extracted from the text: Form 10-K explicitly measures GAAP margin burdened by acquisition restructuring, whereas the Investor Presentation reports Adjusted Non-GAAP margin isolating recurring operational performance.

### Case 4: Audit & Extraction Failure
* **Claim**: Ambiguous capital deployment growth statement.
* **Source Evidence**:
  * `Executive_Strategy_Memo.pdf` (Page 1): *"The newly formed regional subsidiary will accelerate capital deployment by an additional 40% in the coming cycle."*
* **System Reasoning**: The extracted statement suffers from ambiguous referents and underspecified boundaries: the entity ('the newly formed regional subsidiary') is unnamed in the excerpt, the percentage increase lacks an absolute baseline capital expenditure denominator, and the temporal horizon ('in the coming cycle') cannot be grounded to a fiscal quarter or calendar year.
* **Diagnostic Fix**: Enable cross-sentence coreference resolution to link 'the newly formed regional subsidiary' to its legal entity defined upstream; ground relative temporal qualifiers ('coming cycle') against document publication metadata; flag quantitative percentage deltas lacking baseline denominators.

---

## 5. Technical Approach & Architecture

### 1. In-Memory PDF Parser (`PyMuPDF / fitz`)
Reads PDFs page-by-page, capturing text blocks, line boundaries, page numbers, and bounding box coordinates `[x0, y0, x1, y1]`.

### 2. Hybrid Extraction Engine
- **Layer 1 (Document Structure)**: Headings, paragraphs, tables, lists.
- **Layer 2 (Pattern Rules)**: Regex rules for Currency ($/€/£/₹, scale multipliers like million/billion), Percentages, Headcount, Dates/Fiscal periods, Operating Margins.
- **Layer 3 (Local spaCy NLP - `en_core_web_sm`)**: Named Entity Recognition (`ORG`, `PERSON`, `GPE`, `DATE`, `MONEY`, `PERCENT`, `QUANTITY`) + subject-predicate dependency parsing.

### 3. Normalization Engine
Deterministic Python normalizer converting raw strings into comparable representations:
- `$4.2 billion` -> `4,200,000,000 USD`
- `32%` -> `32.0`
- `Q4 2023` -> `{type: 'quarter', year: 2023, quarter: 4}`

### 4. Entity Resolution & Candidate Retrieval
Normalized legal name matching, alias mapping, string similarity clustering, and metric-bucket candidate retrieval to prevent $O(N^2)$ pairwise comparison explosion.

### 5. Multi-Dimensional Relationship Engine
Evaluates candidate pairs across Entity, Metric, Temporal Period, Scope Qualifiers, and Normalized Values to classify into `CORROBORATES`, `CONTRADICTS`, `CONTEXTUALIZES`, `TEMPORAL_CHANGE`, and `UNCERTAIN`.

---

## 6. Limitations and Next Steps

### Limitations
1. **Scanned / Image-Only PDFs**: Text extraction currently relies on digital text layers in PDFs. Scanned image documents without OCR return empty text.
2. **Nested Table Structures**: Dense financial tables with complex multi-column headers require visual layout parsing to preserve row/column relationships.

### Next Steps
* **Tesseract / Document AI OCR Integration**: Add OCR fallback for scanned PDF documents.
* **Interactive Knowledge Graph**: Build PyVis / Cytoscape graph rendering of fact nodes and document relationship edges.
* **Cross-Sentence Coreference Resolution**: Integrate neural coreference models to resolve pronoun references across paragraph boundaries.

---

## 7. License
MIT License. Built for self-contained document intelligence.
