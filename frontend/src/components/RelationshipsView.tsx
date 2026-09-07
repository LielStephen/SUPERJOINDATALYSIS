import React, { useState } from 'react';
import { Relationship } from '../types';
import { Layers, CheckCircle2, AlertTriangle, Scale, HelpCircle, ArrowRight } from 'lucide-react';

interface RelationshipsViewProps {
  relationships: Relationship[];
  onInspectEvidence: (rel: Relationship) => void;
}

export const RelationshipsView: React.FC<RelationshipsViewProps> = ({ relationships, onInspectEvidence }) => {
  const [filterCategory, setFilterCategory] = useState<string>('ALL');

  const filtered = relationships.filter(r => {
    if (filterCategory === 'ALL') return true;
    return r.category === filterCategory;
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div className="card">
        <div className="card-header">
          <div className="card-title">
            <Layers size={18} style={{ color: '#38bdf8' }} />
            <span>Cross-Document Relationship Matrix ({filtered.length} Relationships)</span>
          </div>

          <div style={{ display: 'flex', gap: '8px' }}>
            {['ALL', 'CORROBORATES', 'CONTRADICTS', 'CONTEXTUALIZES', 'UNCERTAIN'].map((cat) => (
              <button
                key={cat}
                className={`tab-button ${filterCategory === cat ? 'active' : ''}`}
                onClick={() => setFilterCategory(cat)}
                style={{ padding: '6px 12px', fontSize: '12px' }}
              >
                {cat}
              </button>
            ))}
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {filtered.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '32px', color: '#94a3b8' }}>
              No relationships match the selected filter.
            </div>
          ) : (
            filtered.map((rel) => (
              <div key={rel.id} className="case-card">
                <div className="case-card-header">
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span className="code-font" style={{ color: '#38bdf8', fontWeight: '600' }}>{rel.id}</span>
                    <span style={{ fontWeight: '600', color: '#f8fafc' }}>
                      {rel.fact_a?.subject} <ArrowRight size={14} style={{ display: 'inline', margin: '0 4px', color: '#94a3b8' }} /> {rel.fact_a?.predicate}
                    </span>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span className="code-font" style={{ fontSize: '12px', color: '#94a3b8' }}>
                      Confidence: {(rel.confidence * 100).toFixed(0)}%
                    </span>
                    {rel.category === 'CORROBORATES' && <span className="badge badge-corroborates">CORROBORATES</span>}
                    {rel.category === 'CONTRADICTS' && <span className="badge badge-contradicts">CONTRADICTS</span>}
                    {rel.category === 'CONTEXTUALIZES' && <span className="badge badge-contextualizes">CONTEXTUALIZES</span>}
                    {rel.category === 'UNCERTAIN' && <span className="badge badge-uncertain">UNCERTAIN</span>}
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '12px' }}>
                  <div className="evidence-quote-box a">
                    <div style={{ fontSize: '11px', color: '#38bdf8', marginBottom: '4px', fontWeight: '600' }}>
                      Fact A ({rel.fact_a?.id}): 📄 {rel.fact_a?.evidence?.filename} (Page {rel.fact_a?.evidence?.page_number})
                    </div>
                    <div style={{ fontWeight: '600', color: '#f8fafc', marginBottom: '4px' }}>
                      Claim: {rel.fact_a?.raw_value}
                    </div>
                    <div style={{ fontStyle: 'italic', fontSize: '12px' }}>"{rel.fact_a?.evidence?.source_text}"</div>
                  </div>

                  <div className="evidence-quote-box b">
                    <div style={{ fontSize: '11px', color: '#c084fc', marginBottom: '4px', fontWeight: '600' }}>
                      Fact B ({rel.fact_b?.id}): 📄 {rel.fact_b?.evidence?.filename} (Page {rel.fact_b?.evidence?.page_number})
                    </div>
                    <div style={{ fontWeight: '600', color: '#f8fafc', marginBottom: '4px' }}>
                      Claim: {rel.fact_b?.raw_value}
                    </div>
                    <div style={{ fontStyle: 'italic', fontSize: '12px' }}>"{rel.fact_b?.evidence?.source_text}"</div>
                  </div>
                </div>

                <div className="reasoning-box">
                  <div style={{ fontWeight: '600', color: '#38bdf8', marginBottom: '4px' }}>Deterministic Reasoning:</div>
                  {rel.reasoning}
                </div>

                {rel.diagnostic_fix && (
                  <div className="diagnostic-box">
                    <div style={{ fontWeight: '600', color: '#f87171', marginBottom: '4px' }}>Diagnostic Fix:</div>
                    {rel.diagnostic_fix}
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
