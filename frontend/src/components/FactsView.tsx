import React, { useState } from 'react';
import { Fact } from '../types';
import { Database, Search, Filter, Eye } from 'lucide-react';

interface FactsViewProps {
  facts: Fact[];
  onSelectFact: (fact: Fact) => void;
}

export const FactsView: React.FC<FactsViewProps> = ({ facts, onSelectFact }) => {
  const [search, setSearch] = useState('');
  const [selectedType, setSelectedType] = useState('ALL');

  const filteredFacts = facts.filter(f => {
    const matchesSearch = 
      f.subject.toLowerCase().includes(search.toLowerCase()) ||
      f.predicate.toLowerCase().includes(search.toLowerCase()) ||
      f.raw_value.toLowerCase().includes(search.toLowerCase()) ||
      (f.evidence?.filename || '').toLowerCase().includes(search.toLowerCase());

    const matchesType = selectedType === 'ALL' || f.fact_type === selectedType;
    return matchesSearch && matchesType;
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div className="card">
        <div className="card-header">
          <div className="card-title">
            <Database size={18} style={{ color: '#38bdf8' }} />
            <span>Structured Fact Registry ({filteredFacts.length} Facts)</span>
          </div>

          <div style={{ display: 'flex', gap: '12px' }}>
            <div style={{ position: 'relative' }}>
              <Search size={15} style={{ position: 'absolute', left: '10px', top: '10px', color: '#94a3b8' }} />
              <input
                type="text"
                placeholder="Search subject, predicate, or metric..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                style={{
                  backgroundColor: '#0b0f19',
                  border: '1px solid #273549',
                  borderRadius: '6px',
                  padding: '8px 12px 8px 32px',
                  color: '#f1f5f9',
                  fontSize: '13px',
                  width: '280px'
                }}
              />
            </div>

            <select
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value)}
              style={{
                backgroundColor: '#0b0f19',
                border: '1px solid #273549',
                borderRadius: '6px',
                padding: '8px 12px',
                color: '#f1f5f9',
                fontSize: '13px'
              }}
            >
              <option value="ALL">All Fact Types</option>
              <option value="CURRENCY">Currency</option>
              <option value="NUMERICAL">Numerical</option>
              <option value="PERCENTAGE">Percentage</option>
            </select>
          </div>
        </div>

        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Fact ID</th>
                <th>Subject Entity</th>
                <th>Predicate</th>
                <th>Raw Claim</th>
                <th>Normalized Value</th>
                <th>Period</th>
                <th>Scope Qualifiers</th>
                <th>Source PDF</th>
                <th>Evidence</th>
              </tr>
            </thead>
            <tbody>
              {filteredFacts.length === 0 ? (
                <tr>
                  <td colSpan={9} style={{ textAlign: 'center', padding: '24px', color: '#94a3b8' }}>
                    No facts match your search criteria.
                  </td>
                </tr>
              ) : (
                filteredFacts.map((fact) => (
                  <tr key={fact.id}>
                    <td className="code-font" style={{ color: '#38bdf8' }}>{fact.id}</td>
                    <td style={{ fontWeight: '600', color: '#f8fafc' }}>{fact.subject}</td>
                    <td style={{ color: '#94a3b8' }}>{fact.predicate}</td>
                    <td style={{ fontWeight: '600', color: '#38bdf8' }}>{fact.raw_value}</td>
                    <td className="code-font" style={{ color: '#10b981' }}>
                      {fact.normalized_str || fact.normalized_value || '—'}
                    </td>
                    <td>
                      <span className="badge badge-type">{fact.temporal_period || 'Unspecified'}</span>
                    </td>
                    <td>
                      {(fact.scope_qualifiers || []).map((q, idx) => (
                        <span key={idx} className="badge badge-type" style={{ marginRight: '4px', background: 'rgba(56, 189, 248, 0.1)', color: '#38bdf8' }}>
                          {q}
                        </span>
                      ))}
                    </td>
                    <td style={{ fontSize: '12px', color: '#94a3b8' }}>
                      📄 {fact.evidence?.filename} (Pg {fact.evidence?.page_number})
                    </td>
                    <td>
                      <button
                        className="btn-secondary"
                        style={{ padding: '4px 8px', fontSize: '12px' }}
                        onClick={() => onSelectFact(fact)}
                      >
                        <Eye size={13} /> View Quote
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
