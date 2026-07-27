import React from 'react';
import { Sparkles, Library, CreditCard, User as UserIcon, LogOut, Zap } from 'lucide-react';

interface NavbarProps {
  activeTab: 'generator' | 'library' | 'pricing';
  setActiveTab: (tab: 'generator' | 'library' | 'pricing') => void;
  user: any;
  onOpenAuth: () => void;
  onLogout: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  user,
  onOpenAuth,
  onLogout,
}) => {
  return (
    <header className="glass-panel" style={{
      margin: 0,
      width: '100%',
      maxWidth: '100%',
      borderRadius: 0,
      borderLeft: 'none',
      borderRight: 'none',
      borderTop: 'none',
      padding: '16px 36px',
      zIndex: 100
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
        
        {/* Brand */}
        <div 
          className="header-brand"
          onClick={() => setActiveTab('generator')}
          style={{ display: 'flex', alignItems: 'center', gap: '12px', cursor: 'pointer' }}
        >
          <div style={{
            background: 'linear-gradient(135deg, #6366F1 0%, #8B5CF6 50%, #10B981 100%)',
            padding: '9px',
            borderRadius: '14px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 0 20px rgba(99, 102, 241, 0.45)'
          }}>
            <Sparkles size={22} color="#FFF" />
          </div>
          <div>
            <h1 style={{ fontSize: '1.35rem', fontWeight: 800, lineHeight: 1.1, margin: 0 }} className="text-gradient">
              QGen <span className="text-gradient-indigo">AI</span>
            </h1>
            <span style={{ fontSize: '0.72rem', color: '#94A3B8', fontWeight: 600, letterSpacing: '0.04em', textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <Zap size={10} color="#10B981" /> Vision Educator Platform
            </span>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="nav-container" style={{

          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          background: 'rgba(15, 23, 42, 0.6)',
          padding: '5px',
          borderRadius: '16px',
          border: '1px solid rgba(255, 255, 255, 0.08)'
        }}>
          <button
            onClick={() => setActiveTab('generator')}
            style={{
              padding: '10px 18px',
              borderRadius: '12px',
              fontWeight: 700,
              fontSize: '0.88rem',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              cursor: 'pointer',
              transition: 'all 0.25s ease',
              background: activeTab === 'generator' ? 'linear-gradient(135deg, rgba(99, 102, 241, 0.25) 0%, rgba(139, 92, 246, 0.2) 100%)' : 'transparent',
              color: activeTab === 'generator' ? '#FFF' : '#94A3B8',
              boxShadow: activeTab === 'generator' ? '0 0 16px rgba(99, 102, 241, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.15)' : 'none',
              border: activeTab === 'generator' ? '1px solid rgba(99, 102, 241, 0.4)' : '1px solid transparent'
            }}

          >
            <Sparkles size={16} color={activeTab === 'generator' ? '#818CF8' : '#64748B'} /> Studio
          </button>

          <button
            onClick={() => setActiveTab('library')}
            style={{
              padding: '10px 18px',
              borderRadius: '12px',
              fontWeight: 700,
              fontSize: '0.88rem',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              border: 'none',
              cursor: 'pointer',
              transition: 'all 0.25s ease',
              background: activeTab === 'library' ? 'linear-gradient(135deg, rgba(99, 102, 241, 0.25) 0%, rgba(139, 92, 246, 0.2) 100%)' : 'transparent',
              color: activeTab === 'library' ? '#FFF' : '#94A3B8',
              boxShadow: activeTab === 'library' ? '0 0 16px rgba(99, 102, 241, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.15)' : 'none',
            }}
          >
            <Library size={16} color={activeTab === 'library' ? '#818CF8' : '#64748B'} /> My Quiz Library
          </button>

          <button
            onClick={() => setActiveTab('pricing')}
            style={{
              padding: '10px 18px',
              borderRadius: '12px',
              fontWeight: 700,
              fontSize: '0.88rem',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              border: 'none',
              cursor: 'pointer',
              transition: 'all 0.25s ease',
              background: activeTab === 'pricing' ? 'linear-gradient(135deg, rgba(99, 102, 241, 0.25) 0%, rgba(139, 92, 246, 0.2) 100%)' : 'transparent',
              color: activeTab === 'pricing' ? '#FFF' : '#94A3B8',
              boxShadow: activeTab === 'pricing' ? '0 0 16px rgba(99, 102, 241, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.15)' : 'none',
            }}
          >
            <CreditCard size={16} color={activeTab === 'pricing' ? '#818CF8' : '#64748B'} /> Pricing & Billing
          </button>
        </nav>

        {/* Auth status */}
        <div>
          {user ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div className="badge badge-indigo" style={{ padding: '8px 16px', borderRadius: '14px', fontSize: '0.85rem' }}>
                <UserIcon size={14} /> {user.full_name || user.email.split('@')[0]}
              </div>
              <button 
                onClick={onLogout} 
                className="btn-secondary" 
                style={{ padding: '8px 12px', borderRadius: '12px' }}
                title="Log out"
              >
                <LogOut size={15} />
              </button>
            </div>
          ) : (
            <button className="btn-primary" onClick={onOpenAuth} style={{ padding: '10px 20px', borderRadius: '12px' }}>
              <UserIcon size={16} /> Educator Sign In
            </button>
          )}
        </div>
      </div>
    </header>
  );
};
