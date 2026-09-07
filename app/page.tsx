'use client'
import React, { useState } from 'react';
import { Upload, FileText, AlertTriangle, CheckCircle, Info, FileQuestion, Loader2 } from 'lucide-react';

export default function FactKnowledgeLayer() {
  const [files, setFiles] = useState<File[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<any[]>([]);
  const [activeTab, setActiveTab] = useState<string>('Corroboration');

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFiles(Array.from(e.target.files));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (files.length === 0) return;

    setLoading(true);
    setError(null);
    setResults([]);

    const formData = new FormData();
    files.forEach(file => formData.append('files', file));

    try {
      const res = await fetch('/api/process-documents', {
        method: 'POST',
        body: formData,
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.error || 'Failed to process documents');
      }

      setResults(data.results);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const getFilteredResults = (category: string) => {
    return results.filter(r => r.category === category);
  };

  const tabs = [
    { id: 'Corroboration', label: 'Corroborated Evidence', icon: CheckCircle },
    { id: 'Contradiction', label: 'Genuine Contradictions', icon: AlertTriangle },
    { id: 'Contextual Reconciliation', label: 'Contextual Reconciliations', icon: Info },
    { id: 'Extraction Failure', label: 'Audit & Failures', icon: FileQuestion },
  ];

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900 p-8">
      <div className="max-w-6xl mx-auto">
        <header className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
            <FileText className="w-8 h-8 text-blue-600" />
            Fact Knowledge Layer
          </h1>
          <p className="text-gray-600 mt-2">Upload multiple documents to extract and cross-reference facts using AI.</p>
        </header>

        <section className="bg-white p-6 rounded-xl shadow-sm border border-gray-200 mb-8">
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Upload PDF Documents</label>
              <input 
                type="file" 
                multiple 
                accept="application/pdf"
                onChange={handleFileChange}
                className="block w-full text-sm text-gray-500
                  file:mr-4 file:py-2 file:px-4
                  file:rounded-md file:border-0
                  file:text-sm file:font-semibold
                  file:bg-blue-50 file:text-blue-700
                  hover:file:bg-blue-100 cursor-pointer"
              />
            </div>
            
            {files.length > 0 && (
              <div className="text-sm text-gray-600">
                {files.length} file(s) selected
              </div>
            )}

            <button 
              type="submit" 
              disabled={files.length === 0 || loading}
              className="self-start px-6 py-2 bg-blue-600 text-white rounded-md font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Upload className="w-5 h-5" />}
              {loading ? 'Processing...' : 'Analyze Documents'}
            </button>
          </form>

          {error && (
            <div className="mt-4 p-4 bg-red-50 text-red-700 rounded-md border border-red-200 flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 shrink-0" />
              <p>{error}</p>
            </div>
          )}
        </section>

        {loading && (
           <div className="flex flex-col items-center justify-center py-12 text-gray-500">
             <Loader2 className="w-10 h-10 animate-spin text-blue-600 mb-4" />
             <p className="text-lg">Extracting and reasoning over facts... This may take a moment.</p>
           </div>
        )}

        {results.length > 0 && !loading && (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
            <div className="flex border-b border-gray-200 overflow-x-auto">
              {tabs.map(tab => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-2 px-6 py-4 text-sm font-medium border-b-2 whitespace-nowrap \${activeTab === tab.id ? 'border-blue-600 text-blue-600 bg-blue-50/50' : 'border-transparent text-gray-500 hover:text-gray-700 hover:bg-gray-50'}`}
                >
                  <tab.icon className="w-4 h-4" />
                  {tab.label}
                  <span className="ml-2 bg-gray-100 text-gray-600 py-0.5 px-2 rounded-full text-xs">
                    {getFilteredResults(tab.id).length}
                  </span>
                </button>
              ))}
            </div>

            <div className="p-6">
              {getFilteredResults(activeTab).length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  No results found for this category.
                </div>
              ) : (
                <div className="flex flex-col gap-6">
                  {getFilteredResults(activeTab).map((result, idx) => (
                    <div key={idx} className="border border-gray-200 rounded-lg p-5 bg-gray-50/50">
                      <div className="mb-4">
                        <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-1">Reasoning</h3>
                        <p className="text-gray-800">{result.reasoning}</p>
                      </div>

                      {result.diagnostic_fix && (
                        <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-md text-yellow-800 text-sm">
                          <strong>Diagnostic Fix:</strong> {result.diagnostic_fix}
                        </div>
                      )}

                      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mt-4">
                        {result.competing_claims?.map((claim: any, cIdx: number) => (
                          <div key={cIdx} className="bg-white p-4 rounded-md border border-gray-200 shadow-sm">
                            <span className="inline-block px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded mb-2 font-medium">
                              Doc: {claim.source_doc}
                            </span>
                            <p className="text-gray-900 font-medium mb-2">{claim.statement}</p>
                            <div className="bg-gray-50 p-3 rounded text-sm text-gray-600 font-mono overflow-x-auto border border-gray-100">
                              "{claim.verbatim_quote}"
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
