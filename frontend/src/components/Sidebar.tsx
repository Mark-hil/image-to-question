import { 
  Sparkles, 
  Library, 
  CreditCard, 
  Code,
  User as UserIcon, 
  LogOut, 
  Plus, 
  PanelLeftClose, 
  PanelLeft, 
  Zap 
} from 'lucide-react';


interface SidebarProps {
  activeTab: 'generator' | 'library' | 'pricing' | 'developer';
  setActiveTab: (tab: 'generator' | 'library' | 'pricing' | 'developer') => void;
  user: any;
  onOpenAuth: () => void;
  onLogout: () => void;
  isCollapsed: boolean;
  setIsCollapsed: (collapsed: boolean) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  setActiveTab,
  user,
  onOpenAuth,
  onLogout,
  isCollapsed,
  setIsCollapsed,
}) => {
  return (
    <aside
      style={{
        width: isCollapsed ? '72px' : '260px',
        minWidth: isCollapsed ? '72px' : '260px',
        height: '100vh',
        position: 'fixed',
        top: 0,
        left: 0,
        backgroundColor: '#070A12',
        borderRight: '1px solid rgba(255, 255, 255, 0.08)',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        padding: isCollapsed ? '16px 10px' : '20px 16px',
        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        zIndex: 1000,
        boxShadow: '4px 0 24px rgba(0, 0, 0, 0.3)',
        overflowY: 'auto',
        overflowX: 'hidden'
      }}
    >
      {/* Top Header & Brand */}
      <div>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: isCollapsed ? 'center' : 'space-between',
            marginBottom: '24px',
            padding: isCollapsed ? '0' : '0 4px'
          }}
        >
          {!isCollapsed && (
            <div 
              onClick={() => setActiveTab('generator')}
              style={{ display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer' }}
            >
              <div style={{
                background: 'linear-gradient(135deg, #6366F1 0%, #8B5CF6 50%, #10B981 100%)',
                padding: '8px',
                borderRadius: '12px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 0 16px rgba(99, 102, 241, 0.4)'
              }}>
                <Sparkles size={20} color="#FFF" />
              </div>
              <div>
                <h1 style={{ fontSize: '1.25rem', fontWeight: 800, lineHeight: 1.1 }} className="text-gradient">
                  QGen <span className="text-gradient-indigo">AI</span>
                </h1>
                <span style={{ fontSize: '0.68rem', color: '#94A3B8', fontWeight: 600, letterSpacing: '0.04em', textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: '3px' }}>
                  <Zap size={9} color="#10B981" /> Vision Platform
                </span>
              </div>
            </div>
          )}

          {isCollapsed && (
            <div 
              onClick={() => setActiveTab('generator')}
              style={{
                background: 'linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%)',
                padding: '8px',
                borderRadius: '12px',
                cursor: 'pointer',
                boxShadow: '0 0 16px rgba(99, 102, 241, 0.4)'
              }}
              title="QGen AI Studio"
            >
              <Sparkles size={20} color="#FFF" />
            </div>
          )}

          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#94A3B8',
              cursor: 'pointer',
              padding: '6px',
              borderRadius: '8px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              transition: 'all 0.2s ease',
            }}
            title={isCollapsed ? "Expand Sidebar" : "Collapse Sidebar"}
          >
            {isCollapsed ? <PanelLeft size={18} /> : <PanelLeftClose size={18} />}
          </button>
        </div>

        {/* ChatGPT Style "New Generation" Action Button */}
        <button
          onClick={() => setActiveTab('generator')}
          style={{
            width: '100%',
            padding: isCollapsed ? '12px 0' : '11px 14px',
            borderRadius: '12px',
            background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.2) 0%, rgba(139, 92, 246, 0.15) 100%)',
            border: '1px solid rgba(99, 102, 241, 0.35)',
            color: '#FFF',
            fontWeight: 700,
            fontSize: '0.88rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: isCollapsed ? 'center' : 'flex-start',
            gap: '10px',
            cursor: 'pointer',
            marginBottom: '24px',
            boxShadow: '0 4px 16px rgba(99, 102, 241, 0.15)',
            transition: 'all 0.25s ease'
          }}
          title="New Question Bank Generation"
        >
          <Plus size={18} color="#818CF8" />
          {!isCollapsed && <span>New Question Studio</span>}
        </button>

        {/* Navigation Section */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          {!isCollapsed && (
            <div style={{
              fontSize: '0.7rem',
              fontWeight: 700,
              color: '#64748B',
              textTransform: 'uppercase',
              letterSpacing: '0.08em',
              padding: '0 8px 8px 8px'
            }}>
              Workspace
            </div>
          )}

          {[
            { id: 'generator', label: 'AI Question Studio', icon: Sparkles, badge: 'VLM' },
            { id: 'library', label: 'My Quiz Library', icon: Library },
            { id: 'pricing', label: 'Pricing & Plans', icon: CreditCard, badge: 'PRO' },
            { id: 'developer', label: 'Developer API', icon: Code, badge: 'API' },
          ].map((item) => {
            const IconComponent = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id as any)}
                style={{
                  width: '100%',
                  padding: isCollapsed ? '12px 0' : '10px 14px',
                  borderRadius: '12px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: isCollapsed ? 'center' : 'space-between',
                  gap: '12px',
                  background: isActive ? 'rgba(255, 255, 255, 0.08)' : 'transparent',
                  color: isActive ? '#FFF' : '#94A3B8',
                  border: isActive ? '1px solid rgba(255, 255, 255, 0.12)' : '1px solid transparent',
                  fontWeight: isActive ? 700 : 600,
                  fontSize: '0.88rem',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease'
                }}
                title={item.label}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <IconComponent size={18} color={isActive ? '#818CF8' : '#64748B'} />
                  {!isCollapsed && <span>{item.label}</span>}
                </div>
                {!isCollapsed && item.badge && (
                  <span style={{
                    fontSize: '0.65rem',
                    fontWeight: 800,
                    padding: '2px 7px',
                    borderRadius: '8px',
                    background: item.badge === 'PRO' ? 'rgba(16, 185, 129, 0.18)' : item.badge === 'API' ? 'rgba(56, 189, 248, 0.18)' : 'rgba(99, 102, 241, 0.18)',
                    color: item.badge === 'PRO' ? '#34D399' : item.badge === 'API' ? '#38BDF8' : '#818CF8',
                    border: `1px solid ${item.badge === 'PRO' ? 'rgba(16, 185, 129, 0.3)' : item.badge === 'API' ? 'rgba(56, 189, 248, 0.3)' : 'rgba(99, 102, 241, 0.3)'}`
                  }}>
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </div>


      {/* Bottom User Footer */}
      <div style={{ borderTop: '1px solid rgba(255, 255, 255, 0.08)', paddingTop: '16px', marginTop: '16px' }}>
        {user ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: isCollapsed ? 'center' : 'space-between',
              padding: isCollapsed ? '8px 0' : '8px 12px',
              borderRadius: '12px',
              background: 'rgba(255, 255, 255, 0.03)',
              border: '1px solid rgba(255, 255, 255, 0.06)'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', overflow: 'hidden' }}>
                <div style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '10px',
                  background: 'linear-gradient(135deg, #6366F1 0%, #4F46E5 100%)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontWeight: 800,
                  fontSize: '0.85rem',
                  color: '#FFF',
                  flexShrink: 0
                }}>
                  {(user.full_name || user.email)[0].toUpperCase()}
                </div>
                {!isCollapsed && (
                  <div style={{ overflow: 'hidden', textAlign: 'left' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#F8FAFC', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: '100px' }}>
                        {user.full_name || user.email.split('@')[0]}
                      </span>
                      <span style={{
                        fontSize: '0.62rem',
                        fontWeight: 800,
                        padding: '1px 6px',
                        borderRadius: '6px',
                        background: user.tier === 'pro' ? 'rgba(16, 185, 129, 0.2)' : user.tier === 'team' ? 'rgba(99, 102, 241, 0.2)' : 'rgba(148, 163, 184, 0.15)',
                        color: user.tier === 'pro' ? '#34D399' : user.tier === 'team' ? '#818CF8' : '#94A3B8',
                        border: `1px solid ${user.tier === 'pro' ? 'rgba(16, 185, 129, 0.3)' : 'rgba(255, 255, 255, 0.1)'}`
                      }}>
                        {(user.tier || 'free').toUpperCase()}
                      </span>
                    </div>
                    <div style={{ fontSize: '0.7rem', color: '#94A3B8', display: 'flex', alignItems: 'center', gap: '4px', marginTop: '2px' }} title={user.next_renewal_date ? `Quota renews on ${user.next_renewal_date}` : undefined}>
                      <Zap size={10} color={user.is_quota_exhausted || user.generations_remaining === 0 ? '#FB7185' : '#10B981'} />
                      <span>{user.monthly_generations_used ?? 0}/{user.monthly_limit ?? 6} used{user.days_until_reset !== undefined ? ` • ${user.days_until_reset}d` : ''}</span>
                    </div>
                  </div>
                )}

              </div>

              {!isCollapsed && (
                <button
                  onClick={onLogout}
                  style={{
                    background: 'transparent',
                    border: 'none',
                    color: '#94A3B8',
                    cursor: 'pointer',
                    padding: '4px',
                    borderRadius: '6px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}
                  title="Sign out"
                >
                  <LogOut size={16} />
                </button>
              )}
            </div>

            {isCollapsed && (
              <button
                onClick={onLogout}
                style={{
                  width: '100%',
                  padding: '8px 0',
                  borderRadius: '10px',
                  background: 'rgba(244, 63, 94, 0.12)',
                  border: '1px solid rgba(244, 63, 94, 0.25)',
                  color: '#FB7185',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}
                title="Sign out"
              >
                <LogOut size={16} />
              </button>
            )}
          </div>
        ) : (
          <button
            onClick={onOpenAuth}
            style={{
              width: '100%',
              padding: isCollapsed ? '12px 0' : '11px 14px',
              borderRadius: '12px',
              background: 'linear-gradient(135deg, #6366F1 0%, #4F46E5 100%)',
              border: 'none',
              color: '#FFF',
              fontWeight: 700,
              fontSize: '0.85rem',
              display: 'flex',
              alignItems: 'center',
              justifyContent: isCollapsed ? 'center' : 'center',
              gap: '8px',
              cursor: 'pointer',
              boxShadow: '0 4px 16px rgba(99, 102, 241, 0.3)'
            }}
            title="Educator Sign In"
          >
            <UserIcon size={16} />
            {!isCollapsed && <span>Educator Sign In</span>}
          </button>
        )}
      </div>
    </aside>
  );
};
