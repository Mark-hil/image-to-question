import React, { useState } from 'react';
import { Check, Sparkles, ExternalLink, ShieldCheck, Zap } from 'lucide-react';
import { api } from '../services/api';

interface PricingPageProps {
  user: any;
  onOpenAuth: () => void;
}

export const PricingPage: React.FC<PricingPageProps> = ({ user, onOpenAuth }) => {
  const [loadingPlan, setLoadingPlan] = useState<string | null>(null);
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'yearly'>('monthly');

  const handlePaystackCheckout = async (planName: string, amountUSD: number) => {
    if (!user) {
      onOpenAuth();
      return;
    }

    setLoadingPlan(planName);
    try {
      const finalAmountUSD = billingCycle === 'yearly' ? amountUSD * 10 : amountUSD;
      const amountNGN = finalAmountUSD * 1500;
      const res = await api.initializePayment(user.email, amountNGN);
      if (res.checkout_url) {
        window.location.href = res.checkout_url;
      }
    } catch (err: any) {
      alert(err.message || 'Failed to initialize Paystack checkout.');
    } finally {
      setLoadingPlan(null);
    }
  };

  return (
    <div className="responsive-padding" style={{ width: '100%', maxWidth: '100%', padding: '24px 36px 60px 36px' }}>
      
      {/* Title */}
      <div style={{ textAlign: 'center', marginBottom: '40px' }}>
        <span className="badge badge-indigo" style={{ marginBottom: '14px', padding: '6px 16px' }}>
          <Sparkles size={14} /> Commercial Educator & Institution Plans
        </span>
        <h2 style={{ fontSize: '2.6rem', fontWeight: 800, marginBottom: '14px' }} className="text-gradient">
          Upgrade Your Assessment Pipeline
        </h2>
        <p style={{ color: '#94A3B8', fontSize: '1.08rem', maxWidth: '640px', margin: '0 auto 28px auto' }}>
          Instantly generate curriculum-aligned question banks with Groq Vision VLM. Export to Microsoft Word (.docx) or Canvas LMS with Paystack billing.
        </p>

        {/* Billing toggle */}
        <div style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '8px',
          background: 'rgba(15, 23, 42, 0.7)',
          padding: '6px',
          borderRadius: '16px',
          border: '1px solid rgba(255, 255, 255, 0.1)'
        }}>
          <button
            onClick={() => setBillingCycle('monthly')}
            style={{
              padding: '8px 18px',
              borderRadius: '12px',
              fontWeight: 700,
              fontSize: '0.88rem',
              border: 'none',
              cursor: 'pointer',
              background: billingCycle === 'monthly' ? '#6366F1' : 'transparent',
              color: billingCycle === 'monthly' ? '#FFF' : '#94A3B8',
              transition: 'all 0.2s ease'
            }}
          >
            Monthly Billing
          </button>
          <button
            onClick={() => setBillingCycle('yearly')}
            style={{
              padding: '8px 18px',
              borderRadius: '12px',
              fontWeight: 700,
              fontSize: '0.88rem',
              border: 'none',
              cursor: 'pointer',
              background: billingCycle === 'yearly' ? '#6366F1' : 'transparent',
              color: billingCycle === 'yearly' ? '#FFF' : '#94A3B8',
              transition: 'all 0.2s ease',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}
          >
            Yearly Billing <span className="badge badge-emerald" style={{ fontSize: '0.7rem', padding: '2px 8px' }}>Save 20%</span>
          </button>
        </div>
      </div>

      {/* Pricing Cards Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '28px', alignItems: 'stretch' }}>
        
        {/* Free Plan */}
        <div className="glass-panel" style={{ padding: '36px 28px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div>
            <span className="badge badge-emerald" style={{ marginBottom: '18px' }}>Starter</span>
            <h3 style={{ fontSize: '1.6rem', fontWeight: 800 }}>Free Educator</h3>
            <p style={{ color: '#94A3B8', fontSize: '0.88rem', marginTop: '4px' }}>Essential AI question generation for single classroom testing.</p>
            
            <div style={{ margin: '20px 0 28px 0' }}>
              <span style={{ fontSize: '2.8rem', fontWeight: 800 }}>$0</span>
              <span style={{ color: '#94A3B8', fontSize: '0.95rem' }}> / {billingCycle === 'yearly' ? 'year' : 'month'}</span>
            </div>

            <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '14px', fontSize: '0.92rem', color: '#CBD5E1' }}>
              <li style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <Check size={18} color="#10B981" /> 1,000 Free Questions / month
              </li>
              <li style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <Check size={18} color="#10B981" /> Standard OCR Text Extraction
              </li>
              <li style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <Check size={18} color="#10B981" /> MCQ & True/False Generator
              </li>
              <li style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <Check size={18} color="#10B981" /> Plain Text (.txt) Export
              </li>
            </ul>
          </div>

          <button className="btn-secondary" style={{ width: '100%', justifyContent: 'center', marginTop: '36px', borderRadius: '12px' }} disabled>
            Current Active Plan
          </button>
        </div>

        {/* Pro Plan */}
        <div className="glass-panel" style={{
          padding: '36px 28px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          border: '2px solid #6366F1',
          boxShadow: '0 0 35px rgba(99, 102, 241, 0.3)',
          position: 'relative',
          background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.12) 0%, rgba(15, 23, 42, 0.85) 100%)'
        }}>
          <div style={{ position: 'absolute', top: '-14px', right: '24px' }}>
            <span className="badge badge-indigo" style={{ background: 'linear-gradient(135deg, #6366F1 0%, #4F46E5 100%)', color: '#FFF', border: 'none', padding: '6px 14px' }}>
              MOST POPULAR
            </span>
          </div>

          <div>
            <span className="badge badge-indigo" style={{ marginBottom: '18px' }}>Pro Educator</span>
            <h3 style={{ fontSize: '1.6rem', fontWeight: 800 }}>Pro Educator</h3>
            <p style={{ color: '#94A3B8', fontSize: '0.88rem', marginTop: '4px' }}>High-speed vision processing with MS Word and Canvas exports.</p>

            <div style={{ margin: '20px 0 28px 0' }}>
              <span style={{ fontSize: '2.8rem', fontWeight: 800, color: '#818CF8' }}>
                ${billingCycle === 'yearly' ? '15' : '19'}
              </span>
              <span style={{ color: '#94A3B8', fontSize: '0.95rem' }}> / month</span>
            </div>

            <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '14px', fontSize: '0.92rem', color: '#CBD5E1' }}>
              <li style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <Check size={18} color="#10B981" /> 10,000 Questions / month
              </li>
              <li style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <Check size={18} color="#10B981" /> Groq Qwen3.6 Vision VLM Engine
              </li>
              <li style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <Check size={18} color="#10B981" /> <strong style={{ color: '#FFF' }}>Microsoft Word (.docx) Export</strong>
              </li>
              <li style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <Check size={18} color="#10B981" /> Canvas LMS QTI 2.1 Zip Export
              </li>
              <li style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <Check size={18} color="#10B981" /> Saved Quiz Library & Online Editor
              </li>
            </ul>
          </div>

          <button
            onClick={() => handlePaystackCheckout('Pro Educator', 19)}
            disabled={loadingPlan === 'Pro Educator'}
            className="btn-primary"
            style={{ width: '100%', justifyContent: 'center', marginTop: '36px', padding: '14px', borderRadius: '12px' }}
          >
            {loadingPlan === 'Pro Educator' ? 'Connecting to Paystack...' : 'Upgrade with Paystack'} <ExternalLink size={16} />
          </button>
        </div>

        {/* Team / School Plan */}
        <div className="glass-panel" style={{ padding: '36px 28px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div>
            <span className="badge badge-purple" style={{ marginBottom: '18px' }}>Institution</span>
            <h3 style={{ fontSize: '1.6rem', fontWeight: 800 }}>School & Department</h3>
            <p style={{ color: '#94A3B8', fontSize: '0.88rem', marginTop: '4px' }}>Multi-teacher seats with shared institution question bank repository.</p>

            <div style={{ margin: '20px 0 28px 0' }}>
              <span style={{ fontSize: '2.8rem', fontWeight: 800 }}>
                ${billingCycle === 'yearly' ? '65' : '79'}
              </span>
              <span style={{ color: '#94A3B8', fontSize: '0.95rem' }}> / month</span>
            </div>

            <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '14px', fontSize: '0.92rem', color: '#CBD5E1' }}>
              <li style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <Check size={18} color="#10B981" /> 50,000 Questions / month
              </li>
              <li style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <Check size={18} color="#10B981" /> 5 Included Teacher Accounts
              </li>
              <li style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <Check size={18} color="#10B981" /> Shared Institution Library
              </li>
              <li style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <Check size={18} color="#10B981" /> Dedicated Priority Processing
              </li>
            </ul>
          </div>

          <button
            onClick={() => handlePaystackCheckout('School & Department', 79)}
            disabled={loadingPlan === 'School & Department'}
            className="btn-primary"
            style={{ width: '100%', justifyContent: 'center', marginTop: '36px', borderRadius: '12px', background: 'linear-gradient(135deg, #10B981 0%, #059669 100%)' }}
          >
            {loadingPlan === 'School & Department' ? 'Connecting to Paystack...' : 'Upgrade Team Plan'} <ExternalLink size={16} />
          </button>
        </div>
      </div>

      {/* Trust Footer */}
      <div className="glass-panel" style={{ marginTop: '48px', padding: '24px', textAlign: 'center', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '24px', flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#94A3B8', fontSize: '0.9rem' }}>
          <ShieldCheck size={20} color="#10B981" /> Secure 256-Bit SSL Paystack Checkout
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#94A3B8', fontSize: '0.9rem' }}>
          <Zap size={20} color="#818CF8" /> Instant Activation
        </div>
      </div>
    </div>
  );
};
