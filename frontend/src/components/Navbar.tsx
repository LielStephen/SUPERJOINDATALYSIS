import React from 'react';
import { Layers, FileText, Database, GitCompare, RefreshCw, AlertCircle } from 'lucide-react';

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  onSeedDemo: () => void;
  isSeeding: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({ activeTab, setActiveTab, onSeedDemo, isSeeding }) => {
  return (
    <header className="header">
      <div className="header-inner">
        <div className="brand">
          <Layers size={22} style={{ color: '#38bdf8' }} />
          <span>Fact Knowledge Layer</span>
          <span className="brand-badge">100% Local Engine</span>
        </div>

        <nav className="nav-tabs">
          <button
            className={`tab-button ${activeTab === 'showcase' ? 'active' : ''}`}
            onClick={() => setActiveTab('showcase')}
          >
            <GitCompare size={16} />
            <span>4 Showcase Cases</span>
          </button>

          <button
            className={`tab-button ${activeTab === 'documents' ? 'active' : ''}`}
            onClick={() => setActiveTab('documents')}
          >
            <FileText size={16} />
            <span>Documents</span>
          </button>

          <button
            className={`tab-button ${activeTab === 'facts' ? 'active' : ''}`}
            onClick={() => setActiveTab('facts')}
          >
            <Database size={16} />
            <span>Fact Explorer</span>
          </button>

          <button
            className={`tab-button ${activeTab === 'relationships' ? 'active' : ''}`}
            onClick={() => setActiveTab('relationships')}
          >
            <Layers size={16} />
            <span>Relationships</span>
          </button>
        </nav>

        <div className="header-actions">
          <button className="btn-secondary" onClick={onSeedDemo} disabled={isSeeding}>
            <RefreshCw size={15} className={isSeeding ? 'spin' : ''} />
            <span>{isSeeding ? 'Extracting...' : '⚡ Seed Demo Dataset'}</span>
          </button>
        </div>
      </div>
    </header>
  );
};
