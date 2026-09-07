import React from 'react';
import { Fact } from '../types';
import { X, FileText, CheckCircle, Database } from 'lucide-react';

interface EvidenceViewerModalProps {
  fact: Fact | null;
  onClose: () => void;
}

export const EvidenceViewerModal: React.FC<EvidenceViewerModalProps> = ({ fact, onClose }) => {
  if (!fact) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-container" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <FileText size={18} style={{ color: '#38bdf8' }} />
            <span style={{ fontWeight: '700', fontSize: '15px' }}>
              Grounding & Source Evidence Viewer ({fact.id})
            </span>
          </div>
          <button
            onClick={onClose}
            style={{ background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer' }}
          >
            <X size={20} />
          </button>
        </div>

        <div className="modal-body">
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '20px' }}>
            <div style={{ background: '#0b0f19', padding: '14px', borderRadius: '6px', border: '1px solid #273549' }}>
              <div style={{ fontSize: '11px', color: '#94a3b8', textTransform: 'uppercase', marginBottom: '4px' }}>Subject Entity</div>
              <div style={{ fontWeight: '600', color: '#f8fafc' }}>{fact.subject}</div>
            </div>

            <div style={{ background: '#0b0f19', padding: '14px', borderRadius: '6px', border: '1px solid #273549' }}>
              <div style={{ fontSize: '11px', color: '#94a3b8', textTransform: 'uppercase', marginBottom: '4px' }}>Predicate / Metric</div>
              <div style={{ fontWeight: '600', color: '#f8fafc' }}>{fact.predicate}</div>
            </div>

            <div style={{ background: '#0b0f19', padding: '14px', borderRadius: '6px', border: '1px solid #273549' }}>
              <div style={{ fontSize: '11px', color: '#94a3b8', textTransform: 'uppercase', marginBottom: '4px' }}>Raw Extracted Value</div>
              <div style={{ fontWeight: '600', color: '#38bdf8' }}>{fact.raw_value}</div>
            </div>

            <div style={{ background: '#0b0f19', padding: '14px', borderRadius: '6px', border: '1px solid #273549' }}>
              <div style={{ fontSize: '11px', color: '#94a3b8', textTransform: 'uppercase', marginBottom: '4px' }}>Normalized Representation</div>
              <div className="code-font" style={{ fontWeight: '600', color: '#10b981' }}>
                {fact.normalized_str || fact.normalized_value || 'N/A'}
              </div>
            </div>
          </div>

          <div style={{ marginBottom: '20px' }}>
            <h4 style={{ fontSize: '13px', fontWeight: '600', marginBottom: '8px', color: '#f8fafc' }}>
              Verbatim Source Text Quote (Page Grounded)
            </h4>
            <div className="evidence-quote-box a" style={{ fontSize: '14px', lineHeight: '1.6' }}>
              "{fact.evidence?.source_text}"
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', background: '#0b0f19', padding: '14px', borderRadius: '6px', border: '1px solid #273549' }}>
            <div style={{ fontSize: '12px', color: '#94a3b8', display: 'flex', justifyContent: 'space-between' }}>
              <span>Source Document:</span>
              <strong style={{ color: '#f8fafc' }}>📄 {fact.evidence?.filename}</strong>
            </div>
            <div style={{ fontSize: '12px', color: '#94a3b8', display: 'flex', justifyContent: 'space-between' }}>
              <span>Page Number:</span>
              <strong style={{ color: '#f8fafc' }}>Page {fact.evidence?.page_number}</strong>
            </div>
            <div style={{ fontSize: '12px', color: '#94a3b8', display: 'flex', justifyContent: 'space-between' }}>
              <span>Bounding Box [x0, y0, x1, y1]:</span>
              <strong className="code-font" style={{ color: '#38bdf8' }}>
                {fact.evidence?.bounding_box ? JSON.stringify(fact.evidence.bounding_box) : 'Captured from PDF block'}
              </strong>
            </div>
            <div style={{ fontSize: '12px', color: '#94a3b8', display: 'flex', justifyContent: 'space-between' }}>
              <span>Temporal Window:</span>
              <strong style={{ color: '#f8fafc' }}>{fact.temporal_period || 'Unspecified'}</strong>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
