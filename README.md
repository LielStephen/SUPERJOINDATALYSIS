# Fact Knowledge Layer: Multi-Document Factual Reconciliation Engine

A self-contained, evidence-grounded document intelligence system built with **Python, FastAPI, PyMuPDF, spaCy, SQLite, and React**.

## Project Objective

The system processes multiple PDF documents and extracts factual claims from them. It then determines how facts from different documents relate to each other.

The system can identify whether two pieces of evidence:

* **CORROBORATE** each other
* **CONTRADICT** each other
* **CONTEXTUALIZE** each other because of differences in scope or accounting
* Represent a **TEMPORAL CHANGE**
* Are **UNCERTAIN** because the available evidence is insufficient

The system is designed to work **locally**. PDFs and extracted text are not sent to Gemini, OpenAI, Claude, or any other external LLM API.

## System Architecture

```text
PDF Document
     │
     ▼
PyMuPDF Parser
     │
     ▼
Fact Extraction Engine
     │
     ├── Document Structure
     ├── Pattern Rules
     └── Local spaCy NLP
     │
     ▼
Normalization Engine
     │
     ▼
Entity Resolution
     │
     ▼
Candidate Matcher
     │
     ▼
Relationship Engine
     │
     ├── CORROBORATES
     ├── CONTRADICTS
     ├── CONTEXTUALIZES
     ├── TEMPORAL_CHANGE
     └── UNCERTAIN
     │
     ▼
SQLite Database
     │
     ▼
FastAPI REST API
     │
     ▼
React Workstation
```

## Core Processing Pipeline

### 1. PDF Parsing

**PyMuPDF / fitz** reads documents page-by-page and preserves:

* Page numbers
* Text blocks
* Line boundaries
* Bounding-box coordinates

This allows every extracted fact to remain connected to its original document evidence.

### 2. Fact Extraction

The extraction engine uses a hybrid approach:

* Document structure analysis
* Regex and deterministic pattern rules
* Local spaCy NLP

It extracts information such as:

* Organizations and entities
* Financial metrics
* Percentages
* Headcount
* Dates
* Fiscal periods
* Operating margins
* Currency values

### 3. Normalization

Raw values are converted into standardized representations so that equivalent facts can be compared.

Examples:

```text
$4.2 billion
→ 4,200,000,000 USD

32%
→ 32.0

Q4 2023
→ {
    type: "quarter",
    year: 2023,
    quarter: 4
  }
```

### 4. Entity Resolution

Different names referring to the same entity are mapped to a canonical entity.

The system uses:

* Legal-name normalization
* Alias mapping
* String similarity
* Entity clustering

### 5. Candidate Matching

Instead of comparing every fact against every other fact, the system groups facts into metric-based buckets and retrieves likely candidates.

This reduces unnecessary **O(N²)** comparisons.

### 6. Relationship Reasoning

Candidate fact pairs are evaluated across multiple dimensions:

* Entity
* Metric
* Temporal period
* Scope
* Qualifiers
* Normalized values

The relationship engine then classifies the evidence.

## Required Demonstration Cases

### Case 1 — Corroborated Evidence

Two documents report the same cloud revenue and year-over-year growth.

The system recognizes that:

* The entities refer to the same business
* The metric is the same
* The reporting period is the same
* The values agree

Result:

```text
CORROBORATES
```

### Case 2 — Genuine Contradiction

Two documents report different global workforce counts for the same reporting date.

Example:

```text
Document A → 14,200 employees
Document B → 15,800 employees
```

The system identifies a direct numerical conflict.

Result:

```text
CONTRADICTS
```

### Case 3 — Contextual Reconciliation

Two documents report different operating margins:

```text
GAAP Operating Margin      → 21.4%
Adjusted Non-GAAP Margin   → 28.6%
```

Rather than incorrectly treating this as a contradiction, the system examines the accounting qualifiers and recognizes that the measurements use different accounting scopes.

Result:

```text
CONTEXTUALIZES
```

### Case 4 — Audit / Extraction Failure

The system encounters an ambiguous statement such as a percentage increase without:

* A clear entity
* An absolute baseline
* A precise time period

Instead of inventing missing information, the system flags the fact as unreliable.

Result:

```text
UNCERTAIN
```

## Technology Stack

| Component      | Technology |
| -------------- | ---------- |
| Language       | Python     |
| API            | FastAPI    |
| PDF Processing | PyMuPDF    |
| NLP            | spaCy      |
| Database       | SQLite     |
| Frontend       | React      |
| Testing        | pytest     |

## Important Design Principle

The central design principle is **evidence-grounded factual reconciliation**.

The system should not simply generate an answer. It should be able to explain:

1. **What fact was extracted**
2. **Where the fact came from**
3. **Which document and page contain the evidence**
4. **Which other facts were compared**
5. **Why the relationship was classified as corroboration, contradiction, contextualization, temporal change, or uncertainty**

This makes the system auditable rather than treating the output as an unexplained prediction.

## Limitations

Current limitations include:

* Scanned/image-only PDFs require OCR.
* Complex nested financial tables may require more advanced layout parsing.
* Cross-sentence references may require additional coreference resolution.

## Future Improvements

Potential extensions include:

* Tesseract/OCR fallback
* Interactive knowledge graph visualization
* Cross-sentence coreference resolution
* More sophisticated table extraction
* Improved entity resolution
* Additional temporal reasoning

## Setup

```bash
git clone https://github.com/LielStephen/SUPERJOINDATALYSIS.git
cd SUPERJOINDATALYSIS

python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run tests:

```bash
python -m pytest backend/tests/test_pipeline.py -v
```

Start the application:

```bash
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

Then open:

```text
http://localhost:8000
```

## License

MIT License.
