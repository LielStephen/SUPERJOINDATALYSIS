---
title: Fact Knowledge Layer
emoji: 🔬
colorFrom: indigo
colorTo: pink
sdk: streamlit
sdk_version: 1.43.0
app_file: app.py
pinned: false
---

# Fact Knowledge Layer: Multi-Document Factual Analysis Engine

An evidence-based factual extraction and cross-referencing system built with Python, Streamlit, and the official Google GenAI SDK (`google-genai`).

The engine acts as a strict, grounded data parser that extracts discrete facts from uploaded PDF documents and performs multi-document cross-referencing with zero hallucinations or reliance on external training knowledge. Every claim is strictly anchored in verbatim source quotations.

---

## Key Features

### 1. Two-Stage Analytical Pipeline
* **Stage 1 — Strict Extraction**: Parses raw PDF text in memory across multiple documents and prompts Gemini to extract atomic facts with exact verbatim quotes, structured metrics/values, source document attribution, and unique IDs (`F-001`, `F-002`, etc.) via Pydantic response schemas (`response_schema`).
* **Stage 2 — Careful Reasoning**: Feeds extracted facts back to Gemini to cross-reference claims across documents. The model identifies subtle differences (such as different fiscal years, varying naming formats, differing scopes, or rounding) and categorizes relationships deterministically into one of four strict classifications.

### 2. Four Specialized Review Views
* **Corroborated Evidence**: Facts verified across multiple documents presented with side-by-side quotations.
* **Genuine Contradictions**: Directly conflicting statements isolated and explained strictly through textual evidence.
* **Contextual Reconciliations**: Seemingly contradictory claims that resolve once factoring in contextual dimensions (e.g. quarterly vs. annual, regional vs. global scope).
* **Audit & Extraction Failures**: Ambiguous statements or incomplete contexts in source PDFs flagged with diagnostic fixes suggesting how to resolve the uncertainty.

### 3. Production Streamlit UI
* **Custom Dark Theme**: Modern dark aesthetic with CSS-driven typography, high-contrast badges, and responsive quote layouts.
* **Metric Counter Strip**: Real-time KPI cards displaying counts for total facts, source documents, corroborations, contradictions, reconciliations, and audit alerts.
* **Full Fact Registry & Raw JSON Export**: Interactive viewer with one-click JSON download buttons for downstream data pipelines.
* **Resilient API & File Handling**: Graceful error interception for Gemini rate limits (`429`), invalid parameters (`400`), and corrupt or unreadable PDF files.

---

## Architecture & Tech Stack

* **Language**: Python 3.10+
* **Frontend / Dashboard**: [Streamlit](https://streamlit.io/)
* **LLM SDK**: [Google GenAI SDK](https://github.com/googleapis/python-genai) (`google-genai`)
* **Schema Validation**: [Pydantic v2](https://docs.pydantic.dev/) (`response_schema` mode for structured JSON)
* **PDF Parser**: [pypdf](https://pypdf.readthedocs.io/) (in-memory extraction with page-level tracking)

---

## Installation & Setup

### 1. Clone Repository
```bash
git clone https://github.com/LielStephen/SUPERJOINDATALYSIS.git
cd SUPERJOINDATALYSIS
```

### 2. Create Virtual Environment
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Gemini API Key
Obtain an API key from [Google AI Studio](https://aistudio.google.com/).

You can provide the key in one of three ways:
* **In the Streamlit UI**: Enter the key in the sidebar password field.
* **Via Environment Variable**:
  ```bash
  # Windows PowerShell
  $env:GEMINI_API_KEY="your_api_key_here"

  # Linux / macOS
  export GEMINI_API_KEY="your_api_key_here"
  ```
* **Via `.env` file**: Copy `.env.example` to `.env` and set `GEMINI_API_KEY`.

---

## Running the Application

Launch the Streamlit dashboard:
```bash
streamlit run app.py
```

The application will start and automatically open at `http://localhost:8501`.

---

## Usage Guide

1. **Enter API Key**: Provide your Gemini API key in the sidebar (auto-detected if set in environment).
2. **Select Model**: Choose a model (e.g., `gemini-2.5-flash` for high speed, or `gemini-2.5-pro` for deep reasoning).
3. **Upload PDFs**: Drag and drop two or more PDF documents into the file uploader.
4. **Run Analysis**: Click **Run Analysis**. Watch the live status spinner as text is extracted and passed through the two-stage pipeline.
5. **Explore Findings**:
   * Navigate between the 4 dashboard tabs to inspect corroborated claims, disputes, reconciliations, and audit alerts.
   * Expand the **Full Fact Registry** to examine all atomic extracted facts.
   * Use **Raw JSON Output & Export** to download the structured results.
6. **Reset or Re-run**: Click **Reset Analysis** in the sidebar to clear state and analyze a new document batch.

---

## Project Structure

```
SUPERJOINDATALYSIS/
├── app.py              # Complete Streamlit Fact Knowledge Layer application
├── requirements.txt    # Project Python dependencies
├── Dockerfile          # Production Docker container configuration
├── .dockerignore       # Docker build ignore rules
├── .env.example        # Environment variable template
├── .gitignore          # Git ignore rules for Python, cache, and secrets
└── README.md           # Documentation and usage guide
```

---

## Deployment Options

### Option 1: Streamlit Community Cloud (Recommended & Free)
1. Push your repository to GitHub: `git push origin main`
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
3. Click **New app**.
4. Select Repository: `LielStephen/SUPERJOINDATALYSIS`, Branch: `main`, Main file path: `app.py`.
5. Under **Advanced settings**, set `GEMINI_API_KEY = "your_key"` in Secrets.
6. Click **Deploy**.

### Option 2: Hugging Face Spaces (Free)
1. Navigate to [huggingface.co/spaces](https://huggingface.co/spaces) and create a new space.
2. Choose **Streamlit** as the Space SDK.
3. Link your GitHub repository or push this repository directly to the Space remote.
4. Add `GEMINI_API_KEY` under Space **Settings > Variables and secrets**.

### Option 3: Docker / Cloud Run / Railway / Render
Build and run locally or push the container:
```bash
docker build -t fact-knowledge-layer .
docker run -p 8501:8501 -e GEMINI_API_KEY="your_api_key" fact-knowledge-layer
```
For Cloud Run, Railway, or Render, link this repository and configure `GEMINI_API_KEY` in the service environment variables.
