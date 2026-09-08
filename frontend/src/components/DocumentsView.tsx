import React, { useRef, useState } from 'react';
import { DocumentItem } from '../types';
import { Upload, FolderUp, FileText, CheckCircle, Clock, AlertCircle, RefreshCw, Files } from 'lucide-react';

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
  const [isDragOver, setIsDragOver] = useState<boolean>(false);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const filesArray = Array.from(e.target.files).filter(f => f.name.toLowerCase().endsWith('.pdf'));
      if (filesArray.length > 0) {
        onUpload(filesArray);
      } else {
        alert('Please select valid PDF (.pdf) files.');
      }
      e.target.value = '';
    }
  };

  const handleFolderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const allFiles = Array.from(e.target.files);
      const pdfFiles = allFiles.filter(f => f.name.toLowerCase().endsWith('.pdf'));
      if (pdfFiles.length === 0) {
        alert('No PDF files found in the selected folder.');
      } else {
        onUpload(pdfFiles);
      }
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
        onUpload(pdfFiles);
      } else {
        alert('No PDF files found in the dropped items.');
      }
      return;
    }

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const pdfFiles = Array.from(e.dataTransfer.files).filter(f => f.name.toLowerCase().endsWith('.pdf'));
      if (pdfFiles.length > 0) {
        onUpload(pdfFiles);
      } else {
        alert('Please drop PDF (.pdf) files.');
      }
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
          <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
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
              title="Select an entire folder containing PDF files"
            >
              <FolderUp size={16} />
              <span>Upload Folder</span>
            </button>

            <button
              className="btn-primary"
              onClick={() => fileInputRef.current?.click()}
              disabled={isUploading}
              title="Select one or multiple PDF files"
            >
              <Upload size={16} />
              <span>{isUploading ? (uploadStatus || 'Processing...') : 'Upload PDF(s)'}</span>
            </button>
          </div>
        </div>

        <p style={{ color: '#94a3b8', fontSize: '13px', marginBottom: '16px' }}>
          Upload arbitrary PDF documents into the Knowledge Layer. You can select multiple PDFs, choose an entire folder, or drag and drop below.
        </p>

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
                  Drag & Drop PDF files or entire folders here
                </span>
                <span style={{ fontSize: '12px', color: '#64748b' }}>
                  or click to browse individual PDF files
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
                    No PDF documents uploaded yet. Click "Upload PDF(s)", "Upload Folder", or "⚡ Seed Demo Dataset".
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
