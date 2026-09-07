import React from 'react';
import { Relationship } from '../types';
import { CheckCircle2, AlertTriangle, Scale, HelpCircle, FileText, ArrowRight } from 'lucide-react';

interface FourCasesSectionProps {
  relationships: Relationship[];
  onInspectEvidence: (rel: Relationship) => void;
}

export const FourCasesSection: React.FC<FourCasesSectionProps> = ({ relationships, onInspectEvidence }) => {
  const corroboration = relationships.find(r => r.category === 'CORROBORATES');
  const contradiction = relationships.find(r => r.category === 'CONTRADICTS');
  const contextual = relationships.find(r => r.category === 'CONTEXTUALIZES');
  const failure = relationships.find(r => r.category === 'UNCERTAIN' && r.diagnostic_fix);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div className="card" style={{ background: 'linear-gradient(180deg, #151c2c 0%, #0d1322 100%)' }}>
        <h2 style={{ fontSize: '18px', fontWeight: '700', marginBottom: '8px', color: '#f8fafc' }}>
          Demonstration of Required Four Challenge Cases
        </h2>
        <p style={{ color: '#94a3b8', fontSize: '13px' }}>
          All document analysis, fact grounding, entity resolution, and relationship logic run inside our <strong>100% local processing pipeline</strong> without external LLMs.
        </p>
      </div>

      <div className="cases-grid">
        {/* Case 1: Corroboration */}
        <div className="case-card">
          <div className="case-card-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <CheckCircle2 size={18} style={{ color: '#10b981' }} />
              <span style={{ fontWeight: '700', fontSize: '15px' }}>1. Corroborated Evidence</span>
            </div>
            <span className="badge badge-corroborates">CORROBORATES (100% Match)</span>
          </div>

          {corroboration ? (
            <div>
              <div className="evidence-quote-box a">
                <div style={{ fontSize: '11px', color: '#38bdf8', marginBottom: '4px', fontWeight: '600' }}>
                  📄 {corroboration.fact_a?.evidence?.filename || 'Document A'} — Page {corroboration.fact_a?.evidence?.page_number || 1}
                </div>
                "{corroboration.fact_a?.evidence?.source_text}"
              </div>

              <div className="evidence-quote-box b">
                <div style={{ fontSize: '11px', color: '#c084fc', marginBottom: '4px', fontWeight: '600' }}>
                  📄 {corroboration.fact_b?.evidence?.filename || 'Document B'} — Page {corroboration.fact_b?.evidence?.page_number || 1}
                </div>
                "{corroboration.fact_b?.evidence?.source_text}"
              </div>

              <div className="reasoning-box">
                <div style={{ fontWeight: '600', color: '#38bdf8', marginBottom: '4px' }}>System Local Reasoning:</div>
                {corroboration.reasoning}
              </div>
            </div>
          ) : (
            <p style={{ color: '#94a3b8', fontStyle: 'italic' }}>Click "⚡ Seed Demo Dataset" above to run live extraction.</p>
          )}
        </div>

        {/* Case 2: Contradiction */}
        <div className="case-card">
          <div className="case-card-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <AlertTriangle size={18} style={{ color: '#ef4444' }} />
              <span style={{ fontWeight: '700', fontSize: '15px' }}>2. Genuine Contradiction</span>
            </div>
            <span className="badge badge-contradicts">CONTRADICTS (Conflict)</span>
          </div>

          {contradiction ? (
            <div>
              <div className="evidence-quote-box a">
                <div style={{ fontSize: '11px', color: '#38bdf8', marginBottom: '4px', fontWeight: '600' }}>
                  📄 {contradiction.fact_a?.evidence?.filename || 'Document A'} — Page {contradiction.fact_a?.evidence?.page_number || 1}
                </div>
                "{contradiction.fact_a?.evidence?.source_text}"
              </div>

              <div className="evidence-quote-box b">
                <div style={{ fontSize: '11px', color: '#c084fc', marginBottom: '4px', fontWeight: '600' }}>
                  📄 {contradiction.fact_b?.evidence?.filename || 'Document B'} — Page {contradiction.fact_b?.evidence?.page_number || 1}
                </div>
                "{contradiction.fact_b?.evidence?.source_text}"
              </div>

              <div className="reasoning-box" style={{ background: 'rgba(239, 68, 68, 0.05)', border: '1px solid rgba(239, 68, 68, 0.2)' }}>
                <div style={{ fontWeight: '600', color: '#f87171', marginBottom: '4px' }}>System Local Reasoning:</div>
                {contradiction.reasoning}
              </div>
            </div>
          ) : (
            <p style={{ color: '#94a3b8', fontStyle: 'italic' }}>Click "⚡ Seed Demo Dataset" above to run live extraction.</p>
          )}
        </div>

        {/* Case 3: Contextual Reconciliation */}
        <div className="case-card">
          <div className="case-card-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Scale size={18} style={{ color: '#f59e0b' }} />
              <span style={{ fontWeight: '700', fontSize: '15px' }}>3. Contextual Difference</span>
            </div>
            <span className="badge badge-contextualizes">CONTEXTUALIZES (Scope)</span>
          </div>

          {contextual ? (
            <div>
              <div className="evidence-quote-box a">
                <div style={{ fontSize: '11px', color: '#38bdf8', marginBottom: '4px', fontWeight: '600' }}>
                  📄 {contextual.fact_a?.evidence?.filename || 'Form 10-K'} — Page {contextual.fact_a?.evidence?.page_number || 1}
                </div>
                "{contextual.fact_a?.evidence?.source_text}"
              </div>

              <div className="evidence-quote-box b">
                <div style={{ fontSize: '11px', color: '#c084fc', marginBottom: '4px', fontWeight: '600' }}>
                  📄 {contextual.fact_b?.evidence?.filename || 'Investor Deck'} — Page {contextual.fact_b?.evidence?.page_number || 1}
                </div>
                "{contextual.fact_b?.evidence?.source_text}"
              </div>

              <div className="reasoning-box" style={{ background: 'rgba(245, 158, 11, 0.05)', border: '1px solid rgba(245, 158, 11, 0.2)' }}>
                <div style={{ fontWeight: '600', color: '#fbbf24', marginBottom: '4px' }}>System Local Reasoning:</div>
                {contextual.reasoning}
              </div>
            </div>
          ) : (
            <p style={{ color: '#94a3b8', fontStyle: 'italic' }}>Click "⚡ Seed Demo Dataset" above to run live extraction.</p>
          )}
        </div>

        {/* Case 4: Audit / Extraction Failure */}
        <div className="case-card">
          <div className="case-card-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <HelpCircle size={18} style={{ color: '#a855f7' }} />
              <span style={{ fontWeight: '700', fontSize: '15px' }}>4. Audit & Extraction Failure</span>
            </div>
            <span className="badge badge-uncertain">UNCERTAIN (Audit Flag)</span>
          </div>

          {failure ? (
            <div>
              <div className="evidence-quote-box a" style={{ borderLeftColor: '#a855f7' }}>
                <div style={{ fontSize: '11px', color: '#c084fc', marginBottom: '4px', fontWeight: '600' }}>
                  📄 {failure.fact_a?.evidence?.filename || 'Executive Strategy Memo'} — Page {failure.fact_a?.evidence?.page_number || 1}
                </div>
                "{failure.fact_a?.evidence?.source_text}"
              </div>

              <div className="reasoning-box" style={{ background: 'rgba(168, 85, 247, 0.05)', border: '1px solid rgba(168, 85, 247, 0.2)' }}>
                <div style={{ fontWeight: '600', color: '#c084fc', marginBottom: '4px' }}>System Diagnostic Reasoning:</div>
                {failure.reasoning}
              </div>

              <div className="diagnostic-box">
                <div style={{ fontWeight: '600', color: '#f87171', marginBottom: '4px' }}>Recommended Diagnostic Fix:</div>
                {failure.diagnostic_fix}
              </div>
            </div>
          ) : (
            <p style={{ color: '#94a3b8', fontStyle: 'italic' }}>Click "⚡ Seed Demo Dataset" above to run live extraction.</p>
          )}
        </div>
      </div>
    </div>
  );
};
