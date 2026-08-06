import React, { useState } from 'react';
import { X, Download, FileArchive, FileText, Copy, Check, FileType } from 'lucide-react';
import { api } from '../services/api';
import type { QuestionData } from '../services/api';

interface ExportModalProps {
  isOpen: boolean;
  onClose: () => void;
  quizTitle: string;
  quizId?: string;
  questions: QuestionData[];
  user?: any;
  onOpenAuth?: () => void;
}

export const ExportModal: React.FC<ExportModalProps> = ({
  isOpen,
  onClose,
  quizTitle,
  quizId,
  questions,
  user,
  onOpenAuth,
}) => {
  const [copied, setCopied] = useState(false);
  const [exportingQti, setExportingQti] = useState(false);
  const [exportingText, setExportingText] = useState(false);
  const [exportingDocx, setExportingDocx] = useState(false);
  const [exportingCsv, setExportingCsv] = useState(false);

  if (!isOpen) return null;

  const exportQuestions = user ? questions : questions.slice(0, 5);

  const handleCopyJson = () => {
    navigator.clipboard.writeText(JSON.stringify(exportQuestions, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleExportCsv = async () => {
    setExportingCsv(true);
    try {
      const token = localStorage.getItem('qgen_jwt_token');
      if (quizId && token) {
        await api.exportQuiz(token, quizId, 'csv', quizTitle);
      } else {
        await api.exportDirect(quizTitle, exportQuestions, 'csv');
      }
    } catch (err: any) {
      alert(err.message || 'Export failed');
    } finally {
      setExportingCsv(false);
    }
  };

  const handleExportDocx = async () => {
    setExportingDocx(true);
    try {
      const token = localStorage.getItem('qgen_jwt_token');
      if (quizId && token) {
        await api.exportQuiz(token, quizId, 'docx', quizTitle);
      } else {
        await api.exportDirect(quizTitle, exportQuestions, 'docx');
      }
    } catch (err: any) {
      alert(err.message || 'Export failed');
    } finally {
      setExportingDocx(false);
    }
  };

  const handleExportQti = async () => {
    setExportingQti(true);
    try {
      const token = localStorage.getItem('qgen_jwt_token');
      if (quizId && token) {
        await api.exportQuiz(token, quizId, 'qti', quizTitle);
      } else {
        await api.exportDirect(quizTitle, exportQuestions, 'qti');
      }
    } catch (err: any) {
      alert(err.message || 'Export failed');
    } finally {
      setExportingQti(false);
    }
  };

  const handleExportText = async () => {
    setExportingText(true);
    try {
      const token = localStorage.getItem('qgen_jwt_token');
      if (quizId && token) {
        await api.exportQuiz(token, quizId, 'text', quizTitle);
      } else {
        await api.exportDirect(quizTitle, exportQuestions, 'text');
      }
    } catch (err: any) {
      alert(err.message || 'Export failed');
    } finally {
      setExportingText(false);
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
      zIndex: 1000,
      padding: '20px'
    }}>
      <div className="glass-panel" style={{ width: '100%', maxWidth: '540px', padding: '28px', position: 'relative' }}>
        <button
          onClick={onClose}
          style={{ position: 'absolute', top: '20px', right: '20px', background: 'none', border: 'none', color: '#94A3B8', cursor: 'pointer' }}
        >
          <X size={20} />
        </button>

        <h3 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: '6px' }}>
          Export Quiz Package
        </h3>
        <p style={{ fontSize: '0.88rem', color: '#94A3B8', marginBottom: '20px' }}>
          Export <strong style={{ color: '#FFF' }}>{quizTitle}</strong> ({exportQuestions.length} Questions) to Word documents, CSV spreadsheets, LMS packages, or printable text.
        </p>

        {!user && questions.length > 5 && (
          <div style={{
            background: 'rgba(245, 158, 11, 0.12)',
            border: '1px solid rgba(245, 158, 11, 0.3)',
            color: '#FBBF24',
            padding: '12px 16px',
            borderRadius: '10px',
            marginBottom: '20px',
            fontSize: '0.82rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '8px'
          }}>
            <span>🔒 <strong>Guest Limit</strong>: Exporting first 5 questions of {questions.length}.</span>
            {onOpenAuth && (
              <button
                onClick={() => {
                  onClose();
                  onOpenAuth();
                }}
                style={{ background: 'none', border: 'none', color: '#FCD34D', cursor: 'pointer', fontSize: '0.8rem', fontWeight: 700, textDecoration: 'underline', whiteSpace: 'nowrap' }}
              >
                Sign In to Export All
              </button>
            )}
          </div>
        )}

        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>

          {/* CSV Spreadsheet */}
          <div style={{
            background: 'rgba(16, 185, 129, 0.1)',
            border: '1px solid rgba(16, 185, 129, 0.3)',
            padding: '16px',
            borderRadius: '12px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div style={{ padding: '10px', background: 'rgba(16, 185, 129, 0.2)', borderRadius: '10px', color: '#34D399' }}>
                <FileType size={24} />
              </div>
              <div>
                <h4 style={{ fontSize: '0.95rem', fontWeight: 600 }}>CSV Spreadsheet Data</h4>
                <span style={{ fontSize: '0.78rem', color: '#94A3B8' }}>Structured CSV with Class, Subject & Bloom's tags (.csv)</span>
              </div>
            </div>
            <button
              onClick={handleExportCsv}
              disabled={exportingCsv}
              className="btn-primary"
              style={{ background: 'linear-gradient(135deg, #059669 0%, #10B981 100%)', padding: '8px 14px', fontSize: '0.85rem' }}
            >
              <Download size={14} /> {exportingCsv ? 'Exporting...' : 'Export .csv'}
            </button>
          </div>
          
          {/* MS Word Document */}
          <div style={{
            background: 'rgba(59, 130, 246, 0.1)',
            border: '1px solid rgba(59, 130, 246, 0.3)',
            padding: '16px',
            borderRadius: '12px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div style={{ padding: '10px', background: 'rgba(59, 130, 246, 0.2)', borderRadius: '10px', color: '#60A5FA' }}>
                <FileType size={24} />
              </div>
              <div>
                <h4 style={{ fontSize: '0.95rem', fontWeight: 600 }}>Microsoft Word Document</h4>
                <span style={{ fontSize: '0.78rem', color: '#94A3B8' }}>Professional doc with Answer Key page (.docx)</span>
              </div>
            </div>
            <button
              onClick={handleExportDocx}
              disabled={exportingDocx}
              className="btn-primary"
              style={{ background: 'linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%)', padding: '8px 14px', fontSize: '0.85rem' }}
            >
              <Download size={14} /> {exportingDocx ? 'Exporting...' : 'Export .docx'}
            </button>
          </div>

          {/* Canvas QTI */}
          <div style={{
            background: 'rgba(255, 255, 255, 0.04)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            padding: '16px',
            borderRadius: '12px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div style={{ padding: '10px', background: 'rgba(99, 102, 241, 0.15)', borderRadius: '10px', color: '#818CF8' }}>
                <FileArchive size={24} />
              </div>
              <div>
                <h4 style={{ fontSize: '0.95rem', fontWeight: 600 }}>Canvas LMS QTI 2.1 Package</h4>
                <span style={{ fontSize: '0.78rem', color: '#94A3B8' }}>1-Click Quiz import for Canvas & Moodle (.zip)</span>
              </div>
            </div>
            <button
              onClick={handleExportQti}
              disabled={exportingQti}
              className="btn-secondary"
              style={{ padding: '8px 14px', fontSize: '0.85rem' }}
            >
              <Download size={14} /> {exportingQti ? 'Exporting...' : 'Export .zip'}
            </button>
          </div>

          {/* Printable Text */}
          <div style={{
            background: 'rgba(255, 255, 255, 0.04)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            padding: '16px',
            borderRadius: '12px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div style={{ padding: '10px', background: 'rgba(16, 185, 129, 0.15)', borderRadius: '10px', color: '#34D399' }}>
                <FileText size={24} />
              </div>
              <div>
                <h4 style={{ fontSize: '0.95rem', fontWeight: 600 }}>Printable Quiz & Answer Key</h4>
                <span style={{ fontSize: '0.78rem', color: '#94A3B8' }}>Formatted plain text document (.txt)</span>
              </div>
            </div>
            <button
              onClick={handleExportText}
              disabled={exportingText}
              className="btn-secondary"
              style={{ padding: '8px 14px', fontSize: '0.85rem' }}
            >
              <Download size={14} /> {exportingText ? 'Exporting...' : 'Export .txt'}
            </button>
          </div>

          {/* JSON Copy */}
          <div style={{
            background: 'rgba(255, 255, 255, 0.04)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            padding: '16px',
            borderRadius: '12px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div style={{ padding: '10px', background: 'rgba(244, 63, 94, 0.15)', borderRadius: '10px', color: '#FB7185' }}>
                <Copy size={24} />
              </div>
              <div>
                <h4 style={{ fontSize: '0.95rem', fontWeight: 600 }}>Developer JSON Payload</h4>
                <span style={{ fontSize: '0.78rem', color: '#94A3B8' }}>Raw questions JSON data array</span>
              </div>
            </div>
            <button onClick={handleCopyJson} className="btn-secondary" style={{ padding: '8px 14px', fontSize: '0.85rem' }}>
              {copied ? <Check size={14} color="#10B981" /> : <Copy size={14} />} {copied ? 'Copied!' : 'Copy JSON'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
