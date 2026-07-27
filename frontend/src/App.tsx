import { useState, useEffect } from 'react';
import './styles/main.css';
import { Navbar } from './components/Navbar';
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
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Navigation Bar */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        user={user}
        onOpenAuth={() => setIsAuthOpen(true)}
        onLogout={handleLogout}
      />

      {/* Main Content Pages */}
      <main style={{ flex: 1, padding: '16px 0' }}>
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
        padding: '24px',
        textAlign: 'center',
        color: '#64748B',
        fontSize: '0.85rem'
      }}>
        <div>QGen AI Platform &copy; 2026 — Vision LLM Educator Question Bank Generator</div>
      </footer>

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
