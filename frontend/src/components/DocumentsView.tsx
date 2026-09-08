import React, { useRef, useState } from 'react';
import { DocumentItem } from '../types';
import { Upload, FolderUp, FileText, CheckCircle, Clock, AlertCircle, RefreshCw, Files, Plus, X, Trash2, Play } from 'lucide-react';

interface DocumentsViewProps {
  documents: DocumentItem[];
  onUpload: (files: File[]) => void;
  onProcess: (docId: string) => void;
  isUploading: boolean;
  uploadStatus?: string;
}

export const DocumentsView: React.FC<DocumentsViewProps> = ({ 
  documents, 
  onUpload, 
  onProcess, 
  isUploading,
  uploadStatus 
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const folderInputRef = useRef<HTMLInputElement>(null);
  const [stagedFiles, setStagedFiles] = useState<File[]>([]);
  const [isDragOver, setIsDragOver] = useState<boolean>(false);

  const addFilesToStage = (newFiles: File[]) => {
    const pdfs = newFiles.filter(f => f.name.toLowerCase().endsWith('.pdf'));
    if (pdfs.length === 0) {
      alert('Please select or drop valid PDF (.pdf) files.');
      return;
    }
    setStagedFiles(prev => {
      const existingKeys = new Set(prev.map(f => `${f.name}_${f.size}`));
      const uniqueNew = pdfs.filter(f => !existingKeys.has(`${f.name}_${f.size}`));
      return [...prev, ...uniqueNew];
    });
  };

  const removeStagedFile = (index: number) => {
    setStagedFiles(prev => prev.filter((_, i) => i !== index));
  };

  const clearStagedFiles = () => {
    setStagedFiles([]);
  };

  const handleStartBatchUpload = () => {
    if (stagedFiles.length === 0) return;
    onUpload(stagedFiles);
    setStagedFiles([]);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      addFilesToStage(Array.from(e.target.files));
      e.target.value = '';
    }
  };

  const handleFolderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      addFilesToStage(Array.from(e.target.files));
      e.target.value = '';
    }
  };

  // Recursively read dropped items (files or nested folders)
  const scanEntry = async (entry: any): Promise<File[]> => {
    if (!entry) return [];
    if (entry.isFile) {
      return new Promise<File[]>((resolve) => {
        entry.file((file: File) => {
          if (file.name.toLowerCase().endsWith('.pdf')) {
            resolve([file]);
          } else {
            resolve([]);
          }
        }, () => resolve([]));
      });
    } else if (entry.isDirectory) {
      const reader = entry.createReader();
      return new Promise<File[]>((resolve) => {
        reader.readEntries(async (entries: any[]) => {
          const subPromises = entries.map(scanEntry);
          const subResults = await Promise.all(subPromises);
          resolve(subResults.flat());
        }, () => resolve([]));
      });
    }
    return [];
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!isUploading) setIsDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
    if (isUploading) return;

    const items = e.dataTransfer.items;
    if (items && items.length > 0) {
      const promises: Promise<File[]>[] = [];
      for (let i = 0; i < items.length; i++) {
        const item = items[i];
        if (item.kind === 'file') {
          const entry = (item as any).webkitGetAsEntry ? (item as any).webkitGetAsEntry() : null;
          if (entry) {
            promises.push(scanEntry(entry));
          } else {
            const f = item.getAsFile();
            if (f && f.name.toLowerCase().endsWith('.pdf')) {
              promises.push(Promise.resolve([f]));
            }
          }
        }
      }
      const collected = await Promise.all(promises);
      const pdfFiles = collected.flat();
      if (pdfFiles.length > 0) {
        addFilesToStage(pdfFiles);
      } else {
        alert('No PDF files found in the dropped items.');
      }
      return;
    }

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const pdfFiles = Array.from(e.dataTransfer.files).filter(f => f.name.toLowerCase().endsWith('.pdf'));
      if (pdfFiles.length > 0) {
        addFilesToStage(pdfFiles);
      } else {
        alert('Please drop valid PDF (.pdf) files.');
      }
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div className="card">
        <div className="card-header" style={{ flexWrap: 'wrap', gap: '12px' }}>
          <div className="card-title">
            <FileText size={18} style={{ color: '#38bdf8' }} />
            <span>Document Ingestion & Management</span>
          </div>

          <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
            {/* Hidden file input for multiple individual PDFs */}
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              accept=".pdf"
              multiple
              style={{ display: 'none' }}
            />

            {/* Hidden directory input for entire folder selection */}
            <input
              type="file"
              ref={folderInputRef}
              onChange={handleFolderChange}
              multiple
              style={{ display: 'none' }}
              {...({ webkitdirectory: '', directory: '' } as any)}
            />

            <button
              className="btn-secondary"
              onClick={() => folderInputRef.current?.click()}
              disabled={isUploading}
              title="Select an entire folder of PDFs to add to queue"
            >
              <FolderUp size={16} />
              <span>+ Select Folder</span>
            </button>

            <button
              className="btn-secondary"
              onClick={() => fileInputRef.current?.click()}
              disabled={isUploading}
              title="Select one or multiple PDF files to add to queue"
            >
              <Plus size={16} />
              <span>+ Select PDFs</span>
            </button>

            {stagedFiles.length > 0 && (
              <button
                className="btn-primary"
                onClick={handleStartBatchUpload}
                disabled={isUploading}
                style={{ background: '#0284c7' }}
              >
                <Play size={14} fill="currentColor" />
                <span>Process Queue ({stagedFiles.length})</span>
              </button>
            )}
          </div>
        </div>

        <p style={{ color: '#94a3b8', fontSize: '13px', marginBottom: '16px' }}>
          You can select multiple PDFs across different folders, drop folders, or queue them up before batch processing.
        </p>

        {/* Staging Queue Area (Visible when user has chosen files across folders) */}
        {stagedFiles.length > 0 && (
          <div style={{
            background: 'rgba(56, 189, 248, 0.05)',
            border: '1px solid rgba(56, 189, 248, 0.3)',
            borderRadius: '8px',
            padding: '16px',
            marginBottom: '20px',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px', flexWrap: 'wrap', gap: '10px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Files size={18} style={{ color: '#38bdf8' }} />
                <span style={{ fontWeight: '600', color: '#f8fafc', fontSize: '14px' }}>
                  Staged Documents Queue ({stagedFiles.length} {stagedFiles.length === 1 ? 'file' : 'files'} ready across folders)
                </span>
              </div>
              
              <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                <button
                  className="btn-secondary"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={isUploading}
                  style={{ padding: '6px 12px', fontSize: '12px' }}
                >
                  <Plus size={13} /> + Add More PDFs
                </button>
                <button
                  className="btn-secondary"
                  onClick={() => folderInputRef.current?.click()}
                  disabled={isUploading}
                  style={{ padding: '6px 12px', fontSize: '12px' }}
                >
                  <FolderUp size={13} /> + Add From Another Folder
                </button>
                <button
                  className="btn-secondary"
                  onClick={clearStagedFiles}
                  disabled={isUploading}
                  style={{ padding: '6px 12px', fontSize: '12px', color: '#f87171', borderColor: 'rgba(239, 68, 68, 0.3)' }}
                  title="Clear staged queue"
                >
                  <Trash2 size={13} /> Clear
                </button>
                <button
                  className="btn-primary"
                  onClick={handleStartBatchUpload}
                  disabled={isUploading}
                  style={{ padding: '6px 16px', fontSize: '13px', fontWeight: '600', background: '#0284c7' }}
                >
                  <Play size={14} fill="currentColor" />
                  <span>Start Processing All ({stagedFiles.length})</span>
                </button>
              </div>
            </div>

            {/* Chips list of staged PDFs */}
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', maxHeight: '180px', overflowY: 'auto', padding: '4px' }}>
              {stagedFiles.map((f, idx) => (
                <div
                  key={`${f.name}-${idx}`}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    background: '#1e293b',
                    border: '1px solid #334155',
                    borderRadius: '6px',
                    padding: '6px 10px',
                    fontSize: '12px',
                    color: '#e2e8f0'
                  }}
                >
                  <span>📄 {f.name}</span>
                  <span style={{ color: '#94a3b8', fontSize: '11px' }}>
                    ({f.size > 1024 * 1024 ? `${(f.size / (1024 * 1024)).toFixed(1)} MB` : `${(f.size / 1024).toFixed(0)} KB`})
                  </span>
                  <button
                    onClick={() => removeStagedFile(idx)}
                    disabled={isUploading}
                    style={{
                      background: 'none',
                      border: 'none',
                      color: '#94a3b8',
                      cursor: 'pointer',
                      padding: '2px',
                      display: 'flex',
                      alignItems: 'center'
                    }}
                    title="Remove this file from queue"
                  >
                    <X size={14} />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Drag & Drop Zone */}
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          style={{
            border: isDragOver ? '2px dashed #38bdf8' : '2px dashed #334155',
            backgroundColor: isDragOver ? 'rgba(56, 189, 248, 0.08)' : 'rgba(15, 23, 42, 0.3)',
            borderRadius: '8px',
            padding: '24px',
            textAlign: 'center',
            marginBottom: '20px',
            transition: 'all 0.2s ease',
            cursor: isUploading ? 'not-allowed' : 'pointer'
          }}
          onClick={() => {
            if (!isUploading) fileInputRef.current?.click();
          }}
        >
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px' }}>
            {isUploading ? (
              <>
                <RefreshCw size={28} className="spin" style={{ color: '#38bdf8' }} />
                <span style={{ fontSize: '14px', fontWeight: '500', color: '#38bdf8' }}>
                  {uploadStatus || 'Processing and extracting facts...'}
                </span>
              </>
            ) : (
              <>
                <div style={{ display: 'flex', gap: '8px', color: isDragOver ? '#38bdf8' : '#94a3b8' }}>
                  <Files size={26} />
                  <FolderUp size={26} />
                </div>
                <span style={{ fontSize: '14px', fontWeight: '500', color: '#f1f5f9' }}>
                  Drag & Drop PDF files or folders here
                </span>
                <span style={{ fontSize: '12px', color: '#64748b' }}>
                  You can drop multiple files and folders at any time to stage them together
                </span>
              </>
            )}
          </div>
        </div>

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
                    No PDF documents uploaded yet. Stage PDF documents above or click "⚡ Seed Demo Dataset".
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
