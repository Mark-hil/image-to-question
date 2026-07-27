import React, { useState } from 'react';
import { X, Lock, Mail, User, ArrowRight, AlertCircle } from 'lucide-react';
import { api } from '../services/api';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (token: string, user: any) => void;
}

export const AuthModal: React.FC<AuthModalProps> = ({ isOpen, onClose, onSuccess }) => {
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (mode === 'register') {
        const res = await api.register(email, password, fullName);
        onSuccess(res.access_token, res.user);
      } else {
        const res = await api.login(email, password);
        onSuccess(res.access_token, res.user);
      }
      onClose();
    } catch (err: any) {
      setError(err.message || 'Authentication error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      background: 'rgba(0, 0, 0, 0.75)',
      backdropFilter: 'blur(8px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1100,
      padding: '20px'
    }}>
      <div className="glass-panel" style={{ width: '100%', maxWidth: '420px', padding: '32px', position: 'relative' }}>
        <button
          onClick={onClose}
          style={{ position: 'absolute', top: '20px', right: '20px', background: 'none', border: 'none', color: '#94A3B8', cursor: 'pointer' }}
        >
          <X size={20} />
        </button>

        {/* Tab Switcher */}
        <div style={{ display: 'flex', borderBottom: '1px solid rgba(255, 255, 255, 0.1)', marginBottom: '24px' }}>
          <button
            onClick={() => { setMode('login'); setError(null); }}
            style={{
              flex: 1,
              padding: '12px',
              background: 'none',
              border: 'none',
              borderBottom: mode === 'login' ? '2px solid #6366F1' : 'none',
              color: mode === 'login' ? '#FFF' : '#94A3B8',
              fontWeight: 600,
              cursor: 'pointer'
            }}
          >
            Sign In
          </button>
          <button
            onClick={() => { setMode('register'); setError(null); }}
            style={{
              flex: 1,
              padding: '12px',
              background: 'none',
              border: 'none',
              borderBottom: mode === 'register' ? '2px solid #6366F1' : 'none',
              color: mode === 'register' ? '#FFF' : '#94A3B8',
              fontWeight: 600,
              cursor: 'pointer'
            }}
          >
            Create Account
          </button>
        </div>

        {error && (
          <div style={{
            background: 'rgba(244, 63, 94, 0.15)',
            border: '1px solid rgba(244, 63, 94, 0.3)',
            color: '#FB7185',
            padding: '10px 14px',
            borderRadius: '8px',
            fontSize: '0.85rem',
            marginBottom: '16px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}>
            <AlertCircle size={16} /> {error}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {mode === 'register' && (
            <div className="form-group">
              <label className="form-label">Full Name</label>
              <div style={{ position: 'relative' }}>
                <User size={16} color="#64748B" style={{ position: 'absolute', left: '12px', top: '12px' }} />
                <input
                  type="text"
                  required
                  placeholder="Dr. Alex Vance"
                  className="input-field"
                  style={{ width: '100%', paddingLeft: '38px' }}
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                />
              </div>
            </div>
          )}

          <div className="form-group">
            <label className="form-label">Email Address</label>
            <div style={{ position: 'relative' }}>
              <Mail size={16} color="#64748B" style={{ position: 'absolute', left: '12px', top: '12px' }} />
              <input
                type="email"
                required
                placeholder="educator@school.edu"
                className="input-field"
                style={{ width: '100%', paddingLeft: '38px' }}
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Password</label>
            <div style={{ position: 'relative' }}>
              <Lock size={16} color="#64748B" style={{ position: 'absolute', left: '12px', top: '12px' }} />
              <input
                type="password"
                required
                placeholder="••••••••"
                className="input-field"
                style={{ width: '100%', paddingLeft: '38px' }}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="btn-primary"
            style={{ width: '100%', justifyContent: 'center', marginTop: '8px', padding: '12px' }}
          >
            {loading ? 'Authenticating...' : mode === 'register' ? 'Register Account' : 'Sign In'} <ArrowRight size={16} />
          </button>
        </form>
      </div>
    </div>
  );
};
