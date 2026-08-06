import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { Key, Code, Copy, Check, Plus, Trash2, Shield, Zap, Terminal, BookOpen, Lock } from 'lucide-react';

interface DeveloperPageProps {
  user: any;
  onOpenAuth: () => void;
}

export const DeveloperPage: React.FC<DeveloperPageProps> = ({ user, onOpenAuth }) => {
  const [tenantId, setTenantId] = useState<string | null>(localStorage.getItem('qgen_tenant_id'));
  const [tenant, setTenant] = useState<any>(null);
  const [apiKeys, setApiKeys] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  // Registration Form
  const [orgName, setOrgName] = useState(user?.full_name ? `${user.full_name}'s Org` : '');
  const [orgEmail, setOrgEmail] = useState(user?.email || '');
  const [isRegistering, setIsRegistering] = useState(false);

  // Create Key Form
  const [newKeyName, setNewKeyName] = useState('');
  const [isCreatingKey, setIsCreatingKey] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);

  // Newly Created Secret Raw Key View
  const [newlyCreatedRawKey, setNewlyCreatedRawKey] = useState<string | null>(null);

  // Code sample tab state
  const [activeCodeTab, setActiveCodeTab] = useState<'curl' | 'python' | 'js'>('curl');

  useEffect(() => {
    if (tenantId) {
      loadTenantData(tenantId);
    }
  }, [tenantId]);

  const loadTenantData = async (tid: string) => {
    setLoading(true);
    try {
      const usage = await api.getTenantUsage(tid);
      setTenant(usage);
      const keys = await api.listApiKeys(tid);
      setApiKeys(keys);
    } catch (err) {
      console.error('Failed to load tenant data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRegisterTenant = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!orgName.trim() || !orgEmail.trim()) {
      alert('Please fill in your organization name and developer email.');
      return;
    }

    setIsRegistering(true);
    try {
      const res = await api.registerTenant(orgName, orgEmail);
      const tid = res.tenant.id;
      localStorage.setItem('qgen_tenant_id', tid);
      setTenantId(tid);
      setTenant(res.tenant);

      if (res.api_key && res.api_key.raw_key) {
        setNewlyCreatedRawKey(res.api_key.raw_key);
      }

      await loadTenantData(tid);
    } catch (err: any) {
      alert(err.message || 'Failed to register developer tenant');
    } finally {
      setIsRegistering(false);
    }
  };

  const handleCreateApiKey = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!tenantId) return;

    setIsCreatingKey(true);
    try {
      const createdKey = await api.createApiKey(tenantId, newKeyName || 'Default Key', 60);
      setNewlyCreatedRawKey(createdKey.raw_key);
      setShowCreateModal(false);
      setNewKeyName('');
      await loadTenantData(tenantId);
    } catch (err: any) {
      alert(err.message || 'Failed to create API key');
    } finally {
      setIsCreatingKey(false);
    }
  };

  const handleRevokeApiKey = async (keyId: string) => {
    if (!tenantId || !confirm('Are you sure you want to revoke this API key? Applications using it will lose access.')) return;
    try {
      await api.revokeApiKey(tenantId, keyId);
      setApiKeys(apiKeys.filter((k) => k.id !== keyId));
    } catch (err: any) {
      alert(err.message || 'Failed to revoke key');
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(text);
    setTimeout(() => setCopiedKey(null), 2500);
  };

  // Code snippets generator
  const getCurlSnippet = () => `curl -X POST "http://localhost:8000/api/generate/upload-and-generate?qtype=mcq&difficulty=medium&num_questions=5" \\
  -H "X-API-Key: YOUR_API_KEY_HERE" \\
  -F "files=@/path/to/worksheet.png" \\
  -F "subject=Physics"`;

  const getPythonSnippet = () => `import requests

url = "http://localhost:8000/api/generate/upload-and-generate"
headers = {"X-API-Key": "YOUR_API_KEY_HERE"}
params = {
    "qtype": "mcq",
    "difficulty": "medium",
    "num_questions": 5,
    "subject": "Physics"
}
files = [("files", open("worksheet.png", "rb"))]

response = requests.post(url, headers=headers, params=params, files=files)
questions = response.json().get("questions", [])
print("Generated Questions:", questions)`;

  const getJsSnippet = () => `const formData = new FormData();
formData.append("files", fileInput.files[0]);

const response = await fetch("http://localhost:8000/api/generate/upload-and-generate?qtype=mcq&num_questions=5", {
  method: "POST",
  headers: {
    "X-API-Key": "YOUR_API_KEY_HERE"
  },
  body: formData
});

const data = await response.json();
console.log("Questions:", data.questions);`;

  if (!user) {
    return (
      <div className="responsive-padding" style={{ width: '100%', maxWidth: '100%', padding: '24px 36px 80px 36px' }}>
        <div style={{ marginBottom: '28px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
            <div style={{ background: 'rgba(99, 102, 241, 0.15)', padding: '10px', borderRadius: '12px', color: '#818CF8' }}>
              <Code size={26} />
            </div>
            <div>
              <h2 style={{ fontSize: '1.8rem', fontWeight: 800 }}>Developer API & Key Management</h2>
              <p style={{ color: '#94A3B8', fontSize: '0.92rem' }}>
                Provision secret API keys, access high-throughput REST endpoints, and integrate AI Question Generation directly into your apps.
              </p>
            </div>
          </div>
        </div>

        <div className="glass-panel" style={{
          padding: '48px 36px',
          maxWidth: '620px',
          margin: '40px auto',
          textAlign: 'center',
          border: '1px solid rgba(239, 68, 68, 0.3)',
          background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.9) 0%, rgba(30, 41, 59, 0.9) 100%)'
        }}>
          <div style={{
            display: 'inline-flex',
            padding: '20px',
            borderRadius: '50%',
            background: 'rgba(239, 68, 68, 0.12)',
            color: '#F87171',
            marginBottom: '20px',
            border: '1px solid rgba(239, 68, 68, 0.3)'
          }}>
            <Lock size={48} />
          </div>

          <h3 style={{ fontSize: '1.6rem', fontWeight: 800, marginBottom: '12px', color: '#F8FAFC' }}>
            Account Required for Developer API
          </h3>
          <p style={{ color: '#94A3B8', fontSize: '0.95rem', lineHeight: 1.6, marginBottom: '28px' }}>
            B2B API key provisioning, rate-limiting, and metered quota tracking require an authenticated account. Please sign in or create a free account to access the Developer Portal.
          </p>

          <button
            onClick={onOpenAuth}
            className="btn-primary"
            style={{
              padding: '14px 28px',
              fontSize: '1rem',
              fontWeight: 700,
              margin: '0 auto',
              background: 'linear-gradient(135deg, #6366F1 0%, #4F46E5 100%)',
              boxShadow: '0 8px 20px rgba(99, 102, 241, 0.3)'
            }}
          >
            🔑 Sign In or Create Free Account
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="responsive-padding" style={{ width: '100%', maxWidth: '100%', padding: '24px 36px 80px 36px' }}>
      
      {/* Header */}
      <div style={{ marginBottom: '28px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
          <div style={{ background: 'rgba(99, 102, 241, 0.15)', padding: '10px', borderRadius: '12px', color: '#818CF8' }}>
            <Code size={26} />
          </div>
          <div>
            <h2 style={{ fontSize: '1.8rem', fontWeight: 800 }}>Developer API & Key Management</h2>
            <p style={{ color: '#94A3B8', fontSize: '0.92rem' }}>
              Provision secret API keys, access high-throughput REST endpoints, and integrate AI Question Generation directly into your apps.
            </p>
          </div>
        </div>
      </div>

      {/* Secret Key Creation Alert Banner */}
      {newlyCreatedRawKey && (
        <div style={{
          background: 'rgba(16, 185, 129, 0.12)',
          border: '1px solid rgba(16, 185, 129, 0.4)',
          borderRadius: '16px',
          padding: '20px 24px',
          marginBottom: '28px',
          position: 'relative'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: '#10B981', fontWeight: 700, fontSize: '1rem', marginBottom: '8px' }}>
            <Shield size={20} /> API Key Successfully Created!
          </div>
          <p style={{ color: '#CBD5E1', fontSize: '0.88rem', marginBottom: '12px' }}>
            Please copy your secret key now. <strong style={{ color: '#F87171' }}>You will not be able to view it again!</strong>
          </p>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', background: 'rgba(15, 23, 42, 0.7)', padding: '10px 16px', borderRadius: '10px', border: '1px solid rgba(255, 255, 255, 0.1)' }}>
            <code style={{ flex: 1, color: '#38BDF8', fontSize: '0.95rem', wordBreak: 'break-all', fontFamily: 'monospace' }}>
              {newlyCreatedRawKey}
            </code>
            <button
              onClick={() => copyToClipboard(newlyCreatedRawKey)}
              className="btn-primary"
              style={{ padding: '6px 14px', fontSize: '0.82rem', whiteSpace: 'nowrap' }}
            >
              {copiedKey === newlyCreatedRawKey ? <Check size={14} /> : <Copy size={14} />}
              {copiedKey === newlyCreatedRawKey ? 'Copied!' : 'Copy Key'}
            </button>
          </div>
          <button
            onClick={() => setNewlyCreatedRawKey(null)}
            style={{ position: 'absolute', top: '16px', right: '16px', background: 'none', border: 'none', color: '#94A3B8', cursor: 'pointer' }}
          >
            ✕
          </button>
        </div>
      )}

      {/* Main Grid Section */}
      <div style={{ display: 'grid', gridTemplateColumns: tenantId ? '1fr 1fr' : '1fr', gap: '28px', marginBottom: '36px' }}>
        
        {/* Registration Panel (if not registered) */}
        {!tenantId ? (
          <div className="glass-panel" style={{ padding: '36px', maxWidth: '640px', margin: '0 auto', width: '100%' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px', color: '#818CF8' }}>
              <Zap size={24} />
              <h3 style={{ fontSize: '1.4rem', fontWeight: 800 }}>Request Developer API Access</h3>
            </div>
            <p style={{ color: '#94A3B8', fontSize: '0.9rem', marginBottom: '24px', lineHeight: 1.5 }}>
              Register your B2B organization to instantly get 1,000 free question generation API credits per month and your secret API Key.
            </p>

            <form onSubmit={handleRegisterTenant} style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#CBD5E1', marginBottom: '6px' }}>
                  Organization / Company Name
                </label>
                <input
                  type="text"
                  className="input-field"
                  placeholder="e.g. EduLearn Technologies"
                  value={orgName}
                  onChange={(e) => setOrgName(e.target.value)}
                  required
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#CBD5E1', marginBottom: '6px' }}>
                  Developer Contact Email
                </label>
                <input
                  type="email"
                  className="input-field"
                  placeholder="developer@company.com"
                  value={orgEmail}
                  onChange={(e) => setOrgEmail(e.target.value)}
                  required
                />
              </div>

              <button
                type="submit"
                disabled={isRegistering}
                className="btn-primary"
                style={{ padding: '14px', fontSize: '0.95rem', justifyContent: 'center', marginTop: '8px' }}
              >
                {isRegistering ? 'Provisioning API Keys...' : '🔑 Register Organization & Get API Keys'}
              </button>
            </form>
          </div>
        ) : (
          /* Tenant Overview & Active Keys */
          <>
            {/* Left Column: API Keys Table */}
            <div className="glass-panel" style={{ padding: '28px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                  <div>
                    <h3 style={{ fontSize: '1.25rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <Key color="#6366F1" size={20} /> Active Secret API Keys
                    </h3>
                    <p style={{ color: '#94A3B8', fontSize: '0.82rem' }}>Organization: {tenant?.name || 'Registered Tenant'}</p>
                  </div>

                  <button
                    onClick={() => setShowCreateModal(true)}
                    className="btn-primary"
                    style={{ padding: '8px 14px', fontSize: '0.82rem' }}
                  >
                    <Plus size={14} /> New API Key
                  </button>
                </div>

                {loading ? (
                  <div style={{ textAlign: 'center', padding: '40px', color: '#94A3B8' }}>Loading API keys...</div>
                ) : apiKeys.length === 0 ? (
                  <div style={{ textAlign: 'center', padding: '30px', color: '#94A3B8' }}>
                    No active API keys found. Click "New API Key" above.
                  </div>
                ) : (
                  <div style={{ overflowX: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
                      <thead>
                        <tr style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.1)', color: '#94A3B8', textAlign: 'left' }}>
                          <th style={{ padding: '10px 12px' }}>Name</th>
                          <th style={{ padding: '10px 12px' }}>Key Prefix</th>
                          <th style={{ padding: '10px 12px' }}>Rate Limit</th>
                          <th style={{ padding: '10px 12px' }}>Status</th>
                          <th style={{ padding: '10px 12px', textAlign: 'right' }}>Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {apiKeys.map((key) => (
                          <tr key={key.id} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.05)' }}>
                            <td style={{ padding: '12px', fontWeight: 600, color: '#F1F5F9' }}>{key.name}</td>
                            <td style={{ padding: '12px', color: '#38BDF8', fontFamily: 'monospace' }}>{key.key_prefix}...</td>
                            <td style={{ padding: '12px', color: '#CBD5E1' }}>{key.rate_limit_rpm || 60} RPM</td>
                            <td style={{ padding: '12px' }}>
                              {key.is_active ? (
                                <span className="badge badge-emerald">Active</span>
                              ) : (
                                <span className="badge" style={{ background: 'rgba(239, 68, 68, 0.15)', color: '#F87171' }}>Revoked</span>
                              )}
                            </td>
                            <td style={{ padding: '12px', textAlign: 'right' }}>
                              {key.is_active && (
                                <button
                                  onClick={() => handleRevokeApiKey(key.id)}
                                  className="btn-danger"
                                  style={{ padding: '4px 8px', fontSize: '0.75rem' }}
                                  title="Revoke Key"
                                >
                                  <Trash2 size={13} /> Revoke
                                </button>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>

            {/* Right Column: Metered Quota Card */}
            <div className="glass-panel" style={{ padding: '28px' }}>
              <h3 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Zap color="#10B981" size={20} /> Developer Quota & Usage
              </h3>

              <div style={{ background: 'rgba(15, 23, 42, 0.6)', padding: '20px', borderRadius: '12px', border: '1px solid rgba(255, 255, 255, 0.08)', marginBottom: '20px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', fontSize: '0.88rem' }}>
                  <span style={{ color: '#94A3B8' }}>Monthly Plan Tier:</span>
                  <span style={{ color: '#10B981', fontWeight: 700, textTransform: 'uppercase' }}>{tenant?.tier || 'Free'} Developer Plan</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px', fontSize: '0.88rem' }}>
                  <span style={{ color: '#94A3B8' }}>Monthly Generation Quota:</span>
                  <span style={{ color: '#F1F5F9', fontWeight: 700 }}>{tenant?.monthly_quota || 1000} API requests/mo</span>
                </div>

                <div style={{ width: '100%', height: '8px', background: 'rgba(255, 255, 255, 0.1)', borderRadius: '4px', overflow: 'hidden' }}>
                  <div style={{ width: '15%', height: '100%', background: 'linear-gradient(90deg, #6366F1 0%, #10B981 100%)' }} />
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '6px', fontSize: '0.75rem', color: '#64748B' }}>
                  <span>150 Used</span>
                  <span>{tenant?.monthly_quota || 1000} Total Quota</span>
                </div>
              </div>

              <div style={{ fontSize: '0.85rem', color: '#94A3B8', lineHeight: 1.5 }}>
                <strong style={{ color: '#CBD5E1', display: 'block', marginBottom: '4px' }}>🔒 Authentication Header:</strong>
                Pass your secret API key in the HTTP header:
                <div style={{ background: 'rgba(0, 0, 0, 0.4)', padding: '8px 12px', borderRadius: '8px', color: '#38BDF8', fontFamily: 'monospace', marginTop: '6px' }}>
                  X-API-Key: qgen_live_...
                </div>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Code Examples & REST API Documentation */}
      <div className="glass-panel" style={{ padding: '32px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <h3 style={{ fontSize: '1.4rem', fontWeight: 800, display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Terminal color="#38BDF8" size={22} /> REST API Interactive Integration Guide
            </h3>
            <p style={{ color: '#94A3B8', fontSize: '0.88rem' }}>
              Endpoint: <code style={{ color: '#818CF8' }}>POST /api/generate/upload-and-generate</code>
            </p>
          </div>

          {/* Language Switcher Tabs */}
          <div style={{ display: 'flex', background: 'rgba(15, 23, 42, 0.7)', padding: '4px', borderRadius: '10px', border: '1px solid rgba(255, 255, 255, 0.08)' }}>
            {(['curl', 'python', 'js'] as const).map((lang) => (
              <button
                key={lang}
                onClick={() => setActiveCodeTab(lang)}
                style={{
                  padding: '6px 16px',
                  borderRadius: '8px',
                  border: 'none',
                  fontSize: '0.82rem',
                  fontWeight: 700,
                  cursor: 'pointer',
                  background: activeCodeTab === lang ? '#6366F1' : 'transparent',
                  color: activeCodeTab === lang ? '#FFF' : '#94A3B8',
                  transition: 'all 0.2s ease'
                }}
              >
                {lang.toUpperCase()}
              </button>
            ))}
          </div>
        </div>

        {/* Code Snippet Box */}
        <div style={{ position: 'relative', background: '#0F172A', borderRadius: '14px', border: '1px solid rgba(255, 255, 255, 0.1)', padding: '20px', marginBottom: '28px' }}>
          <button
            onClick={() => copyToClipboard(
              activeCodeTab === 'curl' ? getCurlSnippet() : activeCodeTab === 'python' ? getPythonSnippet() : getJsSnippet()
            )}
            className="btn-secondary"
            style={{ position: 'absolute', top: '14px', right: '14px', padding: '6px 12px', fontSize: '0.78rem' }}
          >
            {copiedKey ? <Check size={13} /> : <Copy size={13} />} Copy Snippet
          </button>

          <pre style={{ color: '#E2E8F0', fontFamily: 'monospace', fontSize: '0.88rem', overflowX: 'auto', margin: 0, lineHeight: 1.5 }}>
            {activeCodeTab === 'curl' && getCurlSnippet()}
            {activeCodeTab === 'python' && getPythonSnippet()}
            {activeCodeTab === 'js' && getJsSnippet()}
          </pre>
        </div>

        {/* API Parameter Reference Table */}
        <h4 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <BookOpen color="#10B981" size={18} /> Request Parameters Reference
        </h4>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.1)', color: '#94A3B8', textAlign: 'left' }}>
                <th style={{ padding: '10px 12px' }}>Parameter</th>
                <th style={{ padding: '10px 12px' }}>Type</th>
                <th style={{ padding: '10px 12px' }}>Location</th>
                <th style={{ padding: '10px 12px' }}>Description</th>
              </tr>
            </thead>
            <tbody>
              <tr style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.05)' }}>
                <td style={{ padding: '10px 12px', fontFamily: 'monospace', color: '#38BDF8' }}>files</td>
                <td style={{ padding: '10px 12px', color: '#F472B6' }}>File / Multipart</td>
                <td style={{ padding: '10px 12px', color: '#CBD5E1' }}>Form Data</td>
                <td style={{ padding: '10px 12px', color: '#94A3B8' }}>Worksheet photo (.jpg, .png), PDF file, or PowerPoint presentation.</td>
              </tr>
              <tr style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.05)' }}>
                <td style={{ padding: '10px 12px', fontFamily: 'monospace', color: '#38BDF8' }}>num_questions</td>
                <td style={{ padding: '10px 12px', color: '#F472B6' }}>Integer</td>
                <td style={{ padding: '10px 12px', color: '#CBD5E1' }}>Query Param</td>
                <td style={{ padding: '10px 12px', color: '#94A3B8' }}>Number of questions to generate (1 to 100). Default: 3.</td>
              </tr>
              <tr style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.05)' }}>
                <td style={{ padding: '10px 12px', fontFamily: 'monospace', color: '#38BDF8' }}>qtype</td>
                <td style={{ padding: '10px 12px', color: '#F472B6' }}>String</td>
                <td style={{ padding: '10px 12px', color: '#CBD5E1' }}>Query Param</td>
                <td style={{ padding: '10px 12px', color: '#94A3B8' }}><code>mcq</code>, <code>short_answer</code>, <code>true_false</code>, or <code>fill_blank</code>.</td>
              </tr>
              <tr style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.05)' }}>
                <td style={{ padding: '10px 12px', fontFamily: 'monospace', color: '#38BDF8' }}>difficulty</td>
                <td style={{ padding: '10px 12px', color: '#F472B6' }}>String</td>
                <td style={{ padding: '10px 12px', color: '#CBD5E1' }}>Query Param</td>
                <td style={{ padding: '10px 12px', color: '#94A3B8' }}><code>easy</code>, <code>medium</code>, <code>hard</code>, or <code>mixed</code>.</td>
              </tr>
              <tr style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.05)' }}>
                <td style={{ padding: '10px 12px', fontFamily: 'monospace', color: '#38BDF8' }}>blooms_level</td>
                <td style={{ padding: '10px 12px', color: '#F472B6' }}>String</td>
                <td style={{ padding: '10px 12px', color: '#CBD5E1' }}>Query Param</td>
                <td style={{ padding: '10px 12px', color: '#94A3B8' }}>Cognitive classification level (e.g. <code>Understand</code>, <code>Analyze</code>, <code>Apply</code>).</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Create Key Modal */}
      {showCreateModal && (
        <div style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(0,0,0,0.8)',
          backdropFilter: 'blur(8px)',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          zIndex: 1100
        }}>
          <div className="glass-panel" style={{ width: '100%', maxWidth: '480px', padding: '28px' }}>
            <h3 style={{ fontSize: '1.3rem', fontWeight: 800, marginBottom: '16px' }}>Generate Secret API Key</h3>
            
            <form onSubmit={handleCreateApiKey} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#CBD5E1', marginBottom: '6px' }}>
                  Key Name / Description
                </label>
                <input
                  type="text"
                  className="input-field"
                  placeholder="e.g. Production Web Backend"
                  value={newKeyName}
                  onChange={(e) => setNewKeyName(e.target.value)}
                  required
                />
              </div>

              <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end', marginTop: '12px' }}>
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="btn-secondary"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isCreatingKey}
                  className="btn-primary"
                >
                  {isCreatingKey ? 'Creating...' : 'Generate Secret Key'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
