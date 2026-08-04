import { useState, useEffect } from 'react';
import './styles/main.css';
import { Sidebar } from './components/Sidebar';
import { AuthModal } from './components/AuthModal';
import { GeneratorPage } from './pages/GeneratorPage';
import { LibraryPage } from './pages/LibraryPage';
import { PricingPage } from './pages/PricingPage';
import { api } from './services/api';

export function App() {
  const [activeTab, setActiveTab] = useState<'generator' | 'library' | 'pricing'>('generator');
  const [token, setToken] = useState<string | null>(localStorage.getItem('qgen_jwt_token'));
  const [user, setUser] = useState<any>(null);
  const [isAuthOpen, setIsAuthOpen] = useState(false);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);

  useEffect(() => {
    if (token) {
      api.getMe(token)
        .then((userData) => setUser(userData))
        .catch(() => {
          localStorage.removeItem('qgen_jwt_token');
          setToken(null);
          setUser(null);
        });
    }
  }, [token]);

  const handleAuthSuccess = (newToken: string, userData: any) => {
    localStorage.setItem('qgen_jwt_token', newToken);
    setToken(newToken);
    setUser(userData);
  };

  const handleLogout = () => {
    localStorage.removeItem('qgen_jwt_token');
    setToken(null);
    setUser(null);
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', width: '100%', maxWidth: '100vw', overflowX: 'hidden' }}>
      {/* ChatGPT-Style Sidebar */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        user={user}
        onOpenAuth={() => setIsAuthOpen(true)}
        onLogout={handleLogout}
        isCollapsed={isSidebarCollapsed}
        setIsCollapsed={setIsSidebarCollapsed}
      />

      {/* Main Workspace Area */}
      <div style={{ 
        flex: 1, 
        display: 'flex', 
        flexDirection: 'column', 
        minWidth: 0, 
        overflowX: 'hidden',
        marginLeft: isSidebarCollapsed ? '72px' : '260px',
        transition: 'margin-left 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
      }}>
        <main style={{ flex: 1, padding: 0, width: '100%' }}>
          {activeTab === 'generator' && (
            <GeneratorPage
              user={user}
              token={token}
              onOpenAuth={() => setIsAuthOpen(true)}
              onNavigateToLibrary={() => setActiveTab('library')}
            />
          )}

          {activeTab === 'library' && (
            <LibraryPage
              token={token}
              onOpenAuth={() => setIsAuthOpen(true)}
            />
          )}

          {activeTab === 'pricing' && (
            <PricingPage
              user={user}
              onOpenAuth={() => setIsAuthOpen(true)}
            />
          )}
        </main>

        {/* Footer */}
        <footer style={{
          borderTop: '1px solid rgba(255, 255, 255, 0.08)',
          padding: '20px 24px',
          textAlign: 'center',
          color: '#64748B',
          fontSize: '0.85rem'
        }}>
          <div>QGen AI Educator Platform &copy; 2026 — Multimodal Vision LLM Question Bank Studio</div>
        </footer>
      </div>

      {/* Auth Modal */}
      <AuthModal
        isOpen={isAuthOpen}
        onClose={() => setIsAuthOpen(false)}
        onSuccess={handleAuthSuccess}
      />
    </div>
  );
}

export default App;
