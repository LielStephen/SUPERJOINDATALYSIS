import os
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

SAMPLE_DOCS_DIR = Path(__file__).resolve().parent.parent.parent / "sample_pdfs"

SAMPLE_PDF_DEFINITIONS = [
    {
        "filename": "Q4_2023_Earnings_Release.pdf",
        "title": "Q4 2023 Financial Earnings Release",
        "content": [
            "ABC Corporation Reports Fourth Quarter 2023 Results",
            "Cloud Infrastructure segment revenue reached $4.2 billion, representing 32% year-over-year expansion.",
            "Our strong momentum in cloud enterprise adoption drove operating efficiency across all regions."
        ]
    },
    {
        "filename": "FY2023_Shareholder_Letter.pdf",
        "title": "FY2023 Annual Shareholder Letter",
        "content": [
            "Letter to Shareholders - Fiscal Year 2023 Overview",
            "Our cloud business crossed $4.2B in the fourth quarter, growing by 32% compared to the prior year period.",
            "We continue to invest aggressively in next-generation data center infrastructure."
        ]
    },
    {
        "filename": "Global_Workforce_Report_2023.pdf",
        "title": "Global Workforce & Talent Report 2023",
        "content": [
            "Official Headcount Disclosure as of Year-End",
            "Total global permanent headcount as of December 31, 2023 stood at 14,200 full-time employees.",
            "We maintain strict hiring governance across software engineering and product operations."
        ]
    },
    {
        "filename": "Annual_ESG_Disclosure_2023.pdf",
        "title": "Annual ESG & Sustainability Disclosure 2023",
        "content": [
            "Environmental, Social, and Governance Report 2023",
            "The company closed fiscal year 2023 with 15,800 active permanent employees worldwide.",
            "Diversity and workforce sustainability metrics reflect our continued investment in employee wellbeing."
        ]
    },
    {
        "filename": "Form_10K_Annual_Report.pdf",
        "title": "Form 10-K Annual Financial Report",
        "content": [
            "United States Securities and Exchange Commission Form 10-K",
            "GAAP Operating Margin for fiscal year 2023 contracted to 21.4% reflecting acquisition-related restructuring charges.",
            "Consolidated net income reflected one-time transaction expenses."
        ]
    },
    {
        "filename": "Q4_Investor_Presentation.pdf",
        "title": "Q4 Investor Presentation",
        "content": [
            "Executive Investor Deck - FY23 Financial Highlights",
            "Adjusted Non-GAAP Operating Margin for FY23 was 28.6%, reflecting strong core software operational leverage.",
            "Core software margins demonstrate resilient cash generation."
        ]
    },
    {
        "filename": "Executive_Strategy_Memo.pdf",
        "title": "Executive Strategy Memorandum",
        "content": [
            "Internal Corporate Strategy Memo",
            "The newly formed regional subsidiary will accelerate capital deployment by an additional 40% in the coming cycle.",
            "Strategic investments focus on high-growth expansion markets."
        ]
    }
]

def generate_sample_pdfs():
    """Generates real synthetic PDF documents using ReportLab to test PyMuPDF ingestion."""
    os.makedirs(SAMPLE_DOCS_DIR, exist_ok=True)
    generated_paths = []

    for pdf_def in SAMPLE_PDF_DEFINITIONS:
        file_path = SAMPLE_DOCS_DIR / pdf_def["filename"]
        c = canvas.Canvas(str(file_path), pagesize=letter)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, 750, pdf_def["title"])
        
        c.setFont("Helvetica", 11)
        y_pos = 700
        for line in pdf_def["content"]:
            c.drawString(50, y_pos, line)
            y_pos -= 30

        c.showPage()
        c.save()
        generated_paths.append(file_path)

    return generated_paths

if __name__ == "__main__":
    paths = generate_sample_pdfs()
    print(f"Generated {len(paths)} sample PDFs in {SAMPLE_DOCS_DIR}")
