import { DocumentItem, Fact, Relationship } from '../types';

const API_BASE = import.meta.env.VITE_API_URL 
  ? `${import.meta.env.VITE_API_URL.replace(/\/$/, '')}/api` 
  : '/api';

export const fetchDocuments = async (): Promise<DocumentItem[]> => {
  const res = await fetch(`${API_BASE}/documents`);
  if (!res.ok) throw new Error('Failed to fetch documents');
  return res.json();
};

export const fetchFacts = async (docId?: string, factType?: string): Promise<Fact[]> => {
  const params = new URLSearchParams();
  if (docId) params.append('doc_id', docId);
  if (factType) params.append('fact_type', factType);
  const res = await fetch(`${API_BASE}/facts?${params.toString()}`);
  if (!res.ok) throw new Error('Failed to fetch facts');
  return res.json();
};

export const fetchRelationships = async (category?: string): Promise<Relationship[]> => {
  const params = new URLSearchParams();
  if (category) params.append('category', category);
  const res = await fetch(`${API_BASE}/relationships?${params.toString()}`);
  if (!res.ok) throw new Error('Failed to fetch relationships');
  return res.json();
};

export const uploadDocument = async (file: File): Promise<DocumentItem> => {
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch(`${API_BASE}/documents`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) throw new Error('Failed to upload PDF document');
  return res.json();
};

export const processDocument = async (docId: string): Promise<{ status: string; extracted_facts: number }> => {
  const res = await fetch(`${API_BASE}/documents/${docId}/process`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error('Document processing failed');
  return res.json();
};

export const seedDemoDataset = async (): Promise<{ status: string; message: string; documents: string[] }> => {
  const res = await fetch(`${API_BASE}/demo/seed`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error('Demo seeding failed');
  return res.json();
};
