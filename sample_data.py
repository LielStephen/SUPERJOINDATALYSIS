SAMPLE_FACTS = [
    {
        "fact_id": "F-001",
        "statement": "Cloud Infrastructure segment revenue reached $4.2 billion in Q4 2023.",
        "metric_or_value": "$4.2 billion",
        "source_doc": "Q4_2023_Earnings_Release.pdf",
        "verbatim_quote": "Cloud Infrastructure segment revenue reached $4.2 billion, representing 32% year-over-year expansion.",
    },
    {
        "fact_id": "F-002",
        "statement": "Q4 2023 cloud revenue expanded by 32% compared to the prior year.",
        "metric_or_value": "32%",
        "source_doc": "Q4_2023_Earnings_Release.pdf",
        "verbatim_quote": "Cloud Infrastructure segment revenue reached $4.2 billion, representing 32% year-over-year expansion.",
    },
    {
        "fact_id": "F-003",
        "statement": "Fourth quarter cloud business generated $4.2B with 32% annual expansion.",
        "metric_or_value": "$4.2B (32% YoY)",
        "source_doc": "FY2023_Shareholder_Letter.pdf",
        "verbatim_quote": "Our cloud business crossed $4.2B in the fourth quarter, growing by 32% compared to the prior year period.",
    },
    {
        "fact_id": "F-004",
        "statement": "Total global permanent headcount as of December 31, 2023 was 14,200 full-time employees.",
        "metric_or_value": "14,200",
        "source_doc": "Global_Workforce_Report_2023.pdf",
        "verbatim_quote": "Total global permanent headcount as of December 31, 2023 stood at 14,200 full-time employees.",
    },
    {
        "fact_id": "F-005",
        "statement": "The company finished fiscal year 2023 with 15,800 active permanent employees worldwide.",
        "metric_or_value": "15,800",
        "source_doc": "Annual_ESG_Disclosure_2023.pdf",
        "verbatim_quote": "The company closed fiscal year 2023 with 15,800 active permanent employees worldwide.",
    },
    {
        "fact_id": "F-006",
        "statement": "GAAP Operating Margin for fiscal year 2023 contracted to 21.4%.",
        "metric_or_value": "21.4%",
        "source_doc": "Form_10K_Annual_Report.pdf",
        "verbatim_quote": "GAAP Operating Margin for fiscal year 2023 contracted to 21.4% reflecting acquisition-related restructuring charges.",
    },
    {
        "fact_id": "F-007",
        "statement": "Adjusted Non-GAAP Operating Margin for FY23 was reported at 28.6%.",
        "metric_or_value": "28.6%",
        "source_doc": "Q4_Investor_Presentation.pdf",
        "verbatim_quote": "Adjusted Non-GAAP Operating Margin for FY23 was 28.6%, reflecting strong core software operational leverage.",
    },
    {
        "fact_id": "F-008",
        "statement": "The regional subsidiary will accelerate capital deployment by 40% in the coming cycle.",
        "metric_or_value": "40%",
        "source_doc": "Executive_Strategy_Memo.pdf",
        "verbatim_quote": "The newly formed regional subsidiary will accelerate capital deployment by an additional 40% in the coming cycle.",
    },
]

SAMPLE_RELATIONSHIPS = [
    {
        "relationship_id": "R-001",
        "category": "Corroboration",
        "fact_ids": ["F-001", "F-003"],
        "competing_claims": [
            "Cloud Infrastructure segment revenue reached $4.2 billion in Q4 2023.",
            "Fourth quarter cloud business generated $4.2B with 32% annual expansion.",
        ],
        "source_quotes": [
            "Cloud Infrastructure segment revenue reached $4.2 billion, representing 32% year-over-year expansion.",
            "Our cloud business crossed $4.2B in the fourth quarter, growing by 32% compared to the prior year period.",
        ],
        "source_docs": [
            "Q4_2023_Earnings_Release.pdf",
            "FY2023_Shareholder_Letter.pdf",
        ],
        "reasoning": "Both documents confirm identical fourth-quarter cloud financial performance ($4.2 billion revenue and 32% year-over-year growth rate). While the earnings release designates the unit as 'Cloud Infrastructure segment' and the shareholder letter terms it 'our cloud business', the metrics and timeframe align precisely.",
        "diagnostic_fix": None,
    },
    {
        "relationship_id": "R-002",
        "category": "Contradiction",
        "fact_ids": ["F-004", "F-005"],
        "competing_claims": [
            "Total global permanent headcount as of December 31, 2023 was 14,200 full-time employees.",
            "The company finished fiscal year 2023 with 15,800 active permanent employees worldwide.",
        ],
        "source_quotes": [
            "Total global permanent headcount as of December 31, 2023 stood at 14,200 full-time employees.",
            "The company closed fiscal year 2023 with 15,800 active permanent employees worldwide.",
        ],
        "source_docs": [
            "Global_Workforce_Report_2023.pdf",
            "Annual_ESG_Disclosure_2023.pdf",
        ],
        "reasoning": "Direct numerical conflict between two official corporate disclosures for the identical reporting cutoff date (December 31, 2023). The Workforce Report certifies 14,200 full-time employees, whereas the ESG Disclosure states 15,800 active permanent employees. Neither document notes inclusion of contingent workers or divestitures to account for the 1,600 employee discrepancy.",
        "diagnostic_fix": None,
    },
    {
        "relationship_id": "R-003",
        "category": "Contextual Reconciliation",
        "fact_ids": ["F-006", "F-007"],
        "competing_claims": [
            "GAAP Operating Margin for fiscal year 2023 contracted to 21.4%.",
            "Adjusted Non-GAAP Operating Margin for FY23 was reported at 28.6%.",
        ],
        "source_quotes": [
            "GAAP Operating Margin for fiscal year 2023 contracted to 21.4% reflecting acquisition-related restructuring charges.",
            "Adjusted Non-GAAP Operating Margin for FY23 was 28.6%, reflecting strong core software operational leverage.",
        ],
        "source_docs": [
            "Form_10K_Annual_Report.pdf",
            "Q4_Investor_Presentation.pdf",
        ],
        "reasoning": "The 720 basis point difference between 21.4% and 28.6% is fully reconciled by textual accounting context. Form 10-K explicitly measures GAAP margin burdened by one-off 'acquisition-related restructuring charges', while the Investor Presentation presents Adjusted Non-GAAP margin isolating recurring software operations.",
        "diagnostic_fix": None,
    },
    {
        "relationship_id": "R-004",
        "category": "Extraction Failure",
        "fact_ids": ["F-008"],
        "competing_claims": [
            "The regional subsidiary will accelerate capital deployment by 40% in the coming cycle.",
        ],
        "source_quotes": [
            "The newly formed regional subsidiary will accelerate capital deployment by an additional 40% in the coming cycle.",
        ],
        "source_docs": [
            "Executive_Strategy_Memo.pdf",
        ],
        "reasoning": "The extracted claim suffers from ambiguous referents and underspecified boundaries: the entity ('the newly formed regional subsidiary') is unnamed in the excerpt, the percentage increase lacks an absolute baseline capital expenditure number, and the temporal horizon ('in the coming cycle') cannot be grounded to a fiscal quarter or calendar year.",
        "diagnostic_fix": "Enable cross-sentence coreference resolution to link 'the newly formed regional subsidiary' to its legal entity defined in upstream text; anchor relative temporal qualifiers ('coming cycle') against the publication date of the strategy memo; flag quantitative delta claims lacking baseline denominators.",
    },
]
