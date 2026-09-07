import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { FourCasesSection } from './components/FourCasesSection';
import { DocumentsView } from './components/DocumentsView';
import { FactsView } from './components/FactsView';
import { RelationshipsView } from './components/RelationshipsView';
import { EvidenceViewerModal } from './components/EvidenceViewerModal';
import { DocumentItem, Fact, Relationship } from './types';
import { fetchDocuments, fetchFacts, fetchRelationships, uploadDocument, processDocument, seedDemoDataset } from './api/client';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>('showcase');
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [facts, setFacts] = useState<Fact[]>([]);
  const [relationships, setRelationships] = useState<Relationship[]>([]);
  
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [isSeeding, setIsSeeding] = useState<boolean>(false);

  const [selectedFact, setSelectedFact] = useState<Fact | null>(null);

  const loadAllData = async () => {
    setIsLoading(true);
    try {
      const [docsData, factsData, relsData] = await Promise.all([
        fetchDocuments(),
        fetchFacts(),
        fetchRelationships(),
      ]);
      setDocuments(docsData);
      setFacts(factsData);
      setRelationships(relsData);
    } catch (err) {
      console.error('Failed to load data:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadAllData();
  }, []);

  const handleSeedDemo = async () => {
    setIsSeeding(true);
    try {
      await seedDemoDataset();
      await loadAllData();
    } catch (err) {
      alert('Failed to seed demo dataset.');
    } finally {
      setIsSeeding(false);
    }
  };

  const handleUploadDocument = async (file: File) => {
    setIsUploading(true);
    try {
      const newDoc = await uploadDocument(file);
      await processDocument(newDoc.id);
      await loadAllData();
    } catch (err) {
      alert('PDF Upload or Processing failed.');
    } finally {
      setIsUploading(false);
    }
  };

  const handleProcessDocument = async (docId: string) => {
    try {
      await processDocument(docId);
      await loadAllData();
    } catch (err) {
      alert('Document processing failed.');
    }
  };

  return (
    <div className="app-container">
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onSeedDemo={handleSeedDemo}
        isSeeding={isSeeding}
      />

      <main className="main-content">
        {activeTab === 'showcase' && (
          <FourCasesSection
            relationships={relationships}
            onInspectEvidence={(rel) => setSelectedFact(rel.fact_a || null)}
          />
        )}

        {activeTab === 'documents' && (
          <DocumentsView
            documents={documents}
            onUpload={handleUploadDocument}
            onProcess={handleProcessDocument}
            isUploading={isUploading}
          />
        )}

        {activeTab === 'facts' && (
          <FactsView
            facts={facts}
            onSelectFact={(fact) => setSelectedFact(fact)}
          />
        )}

        {activeTab === 'relationships' && (
          <RelationshipsView
            relationships={relationships}
            onInspectEvidence={(rel) => setSelectedFact(rel.fact_a || null)}
          />
        )}
      </main>

      <EvidenceViewerModal
        fact={selectedFact}
        onClose={() => setSelectedFact(null)}
      />
    </div>
  );
};

export default App;
