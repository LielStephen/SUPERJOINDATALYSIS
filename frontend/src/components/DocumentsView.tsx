import React, { useRef } from 'react';
import { DocumentItem } from '../types';
import { Upload, FileText, CheckCircle, Clock, AlertCircle, RefreshCw } from 'lucide-react';

interface DocumentsViewProps {
  documents: DocumentItem[];
  onUpload: (file: File) => void;
  onProcess: (docId: string) => void;
  isUploading: boolean;
}

export const DocumentsView: React.FC<DocumentsViewProps> = ({ documents, onUpload, onProcess, isUploading }) => {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      onUpload(e.target.files[0]);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div className="card">
        <div className="card-header">
          <div className="card-title">
            <FileText size={18} style={{ color: '#38bdf8' }} />
            <span>Document Ingestion & Management</span>
          </div>
          <div>
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              accept=".pdf"
              style={{ display: 'none' }}
            />
            <button
              className="btn-primary"
              onClick={() => fileInputRef.current?.click()}
              disabled={isUploading}
            >
              <Upload size={16} />
              <span>{isUploading ? 'Uploading PDF...' : 'Upload PDF Document'}</span>
            </button>
          </div>
        </div>

        <p style={{ color: '#94a3b8', fontSize: '13px', marginBottom: '16px' }}>
          Upload arbitrary PDF documents into the Knowledge Layer. Text is parsed page-by-page preserving structural block positions and bounding boxes.
        </p>

        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Filename</th>
                <th>Doc ID</th>
                <th>Page Count</th>
                <th>Status</th>
                <th>Facts Extracted</th>
                <th>Upload Date</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {documents.length === 0 ? (
                <tr>
                  <td colSpan={7} style={{ textAlign: 'center', padding: '24px', color: '#94a3b8' }}>
                    No PDF documents uploaded yet. Click "Upload PDF Document" or "⚡ Seed Demo Dataset".
                  </td>
                </tr>
              ) : (
                documents.map((doc) => (
                  <tr key={doc.id}>
                    <td style={{ fontWeight: '600', color: '#f8fafc' }}>
                      📄 {doc.filename}
                    </td>
                    <td className="code-font" style={{ color: '#38bdf8' }}>{doc.id}</td>
                    <td>{doc.page_count} pages</td>
                    <td>
                      {doc.processing_status === 'COMPLETED' && (
                        <span className="badge badge-corroborates">
                          <CheckCircle size={12} /> COMPLETED
                        </span>
                      )}
                      {doc.processing_status === 'PROCESSING' && (
                        <span className="badge badge-contextualizes">
                          <RefreshCw size={12} className="spin" /> PROCESSING
                        </span>
                      )}
                      {doc.processing_status === 'PENDING' && (
                        <span className="badge badge-type">
                          <Clock size={12} /> PENDING
                        </span>
                      )}
                      {doc.processing_status === 'FAILED' && (
                        <span className="badge badge-contradicts">
                          <AlertCircle size={12} /> FAILED
                        </span>
                      )}
                    </td>
                    <td style={{ fontWeight: '600', color: '#10b981' }}>{doc.fact_count} facts</td>
                    <td style={{ color: '#94a3b8', fontSize: '12px' }}>
                      {new Date(doc.upload_date).toLocaleString()}
                    </td>
                    <td>
                      <button
                        className="btn-secondary"
                        style={{ padding: '4px 10px', fontSize: '12px' }}
                        onClick={() => onProcess(doc.id)}
                        disabled={doc.processing_status === 'PROCESSING'}
                      >
                        Run Local Extraction
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
