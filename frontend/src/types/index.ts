export interface FactEvidence {
  id?: string;
  fact_id?: string;
  document_id: string;
  filename: string;
  page_number: number;
  source_text: string;
  bounding_box?: number[] | null;
}

export interface Fact {
  id: string;
  document_id: string;
  subject: string;
  predicate: string;
  raw_value: string;
  fact_type: string;
  normalized_value?: number | null;
  normalized_str?: string | null;
  unit?: string | null;
  currency?: string | null;
  temporal_type?: string | null;
  temporal_year?: number | null;
  temporal_quarter?: number | null;
  temporal_period?: string | null;
  scope_qualifiers?: string[];
  confidence: number;
  entity_id?: string | null;
  evidence?: FactEvidence | null;
}

export interface DocumentItem {
  id: string;
  filename: string;
  page_count: number;
  processing_status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
  upload_date: string;
  fact_count: number;
  pages?: any[];
}

export interface Relationship {
  id: string;
  category: 'CORROBORATES' | 'CONTRADICTS' | 'CONTEXTUALIZES' | 'TEMPORAL_CHANGE' | 'PARTIALLY_SUPPORTS' | 'UNCERTAIN';
  fact_id_a: string;
  fact_id_b: string;
  fact_a?: Fact | null;
  fact_b?: Fact | null;
  confidence: number;
  reasoning: string;
  diagnostic_fix?: string | null;
  context_diffs?: Record<string, any> | null;
}
