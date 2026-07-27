import React, { useState } from 'react';
import { Dropzone } from '../components/Dropzone';
import { QuestionCard } from '../components/QuestionCard';
import { ExportModal } from '../components/ExportModal';
import { api } from '../services/api';
import type { QuestionData } from '../services/api';
import { Sparkles, Sliders, Save, Download, AlertCircle, BookOpen, Plus, Minus, CheckCircle, Award } from 'lucide-react';

interface GeneratorPageProps {
  user: any;
  token: string | null;
  onOpenAuth: () => void;
  onNavigateToLibrary: () => void;
}

export const GeneratorPage: React.FC<GeneratorPageProps> = ({
  user,
  token,
  onOpenAuth,
  onNavigateToLibrary
}) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [qtype, setQtype] = useState<string>('mcq');
  const [difficulty, setDifficulty] = useState<string>('medium');
  const [numQuestions, setNumQuestions] = useState<number>(10);
  const [subject, setSubject] = useState<string>('Biology');
  const [quizTitle, setQuizTitle] = useState<string>('My Quiz Bank');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [questions, setQuestions] = useState<QuestionData[]>([]);

  const [savedQuizId, setSavedQuizId] = useState<string | undefined>(undefined);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [isExportOpen, setIsExportOpen] = useState(false);

  const handleGenerate = async () => {
    if (!selectedFile) {
      setError('Please upload a worksheet photo or PDF document first.');
      return;
    }

    setError(null);
    setLoading(true);
    setSaveSuccess(false);

    try {
      const generated = await api.uploadAndGenerate(
        selectedFile,
        qtype,
        difficulty,
        numQuestions,
        subject
      );
      setQuestions(generated);
      if (selectedFile.name) {
        setQuizTitle(selectedFile.name.replace(/\.[^/.]+$/, "") + " Quiz");
      }
    } catch (err: any) {
      setError(err.message || 'Error generating questions.');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateQuestion = (index: number, updated: QuestionData) => {
    const list = [...questions];
    list[index] = updated;
    setQuestions(list);
  };

  const handleDeleteQuestion = (index: number) => {
    setQuestions(questions.filter((_, i) => i !== index));
  };

  const handleSaveToLibrary = async () => {
    if (!token || !user) {
      onOpenAuth();
      return;
    }

    try {
      const saved = await api.saveQuiz(token, quizTitle, subject, selectedFile?.name, questions);
      setSavedQuizId(saved.id);
      setSaveSuccess(true);
    } catch (err: any) {
      setError(err.message || 'Failed to save quiz bank.');
    }
  };

  return (
    <div className="responsive-padding" style={{ width: '100%', maxWidth: '100%', padding: '24px 36px 50px 36px' }}>
      
      {/* Hero Header */}
      <div className="glass-panel" style={{
        padding: '36px',
        marginBottom: '28px',
        background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.16) 0%, rgba(139, 92, 246, 0.12) 50%, rgba(16, 185, 129, 0.08) 100%)',
        position: 'relative',
        overflow: 'hidden',
        border: '1px solid rgba(99, 102, 241, 0.25)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#818CF8', fontWeight: 700, fontSize: '0.85rem', textTransform: 'uppercase', marginBottom: '10px', flexWrap: 'wrap' }}>
          <span className="badge badge-indigo"><Sparkles size={12} /> Groq Vision Qwen3.6 VLM</span>
          <span className="badge badge-emerald"><Award size={12} /> 100% Curriculum Aligned</span>
        </div>
        <h2 style={{ fontSize: '2.3rem', fontWeight: 800, marginBottom: '10px' }} className="text-gradient">
          Worksheet & Textbook <span className="text-gradient-indigo">AI Question Studio</span>
        </h2>
        <p style={{ color: '#94A3B8', maxWidth: '720px', fontSize: '1rem', lineHeight: 1.6 }}>
          Transform any textbook photo, diagram, or PDF worksheet into standard-aligned question banks (MCQs, Short Answer, True/False) ready for MS Word (.docx) or Canvas LMS export.
        </p>
      </div>

      {/* Upload & Controls Grid */}
      <div className="responsive-grid-2" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '28px', marginBottom: '36px' }}>

        
        {/* Left: Dropzone Panel */}
        <div className="glass-panel" style={{ padding: '28px' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '18px', display: 'flex', alignItems: 'center', gap: '10px' }}>
            <BookOpen size={20} color="#818CF8" /> 1. Upload Source File
          </h3>
          <Dropzone selectedFile={selectedFile} onFileSelect={setSelectedFile} />
        </div>

        {/* Right: Controls Panel */}
        <div className="glass-panel" style={{ padding: '28px' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '18px', display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Sliders size={20} color="#818CF8" /> 2. Question Options
          </h3>

          {/* Question Type Visual Options */}
          <div style={{ marginBottom: '18px' }}>
            <label className="form-label" style={{ marginBottom: '8px' }}>Question Format</label>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px' }}>
              {[
                { id: 'mcq', label: 'MCQ', desc: 'Multiple Choice' },
                { id: 'true_false', label: 'True/False', desc: 'Binary' },
                { id: 'short_answer', label: 'Short Answer', desc: 'Open Text' }
              ].map((item) => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => setQtype(item.id)}
                  style={{
                    padding: '10px 8px',
                    borderRadius: '12px',
                    border: `1px solid ${qtype === item.id ? '#6366F1' : 'rgba(255, 255, 255, 0.08)'}`,
                    background: qtype === item.id ? 'rgba(99, 102, 241, 0.2)' : 'rgba(255, 255, 255, 0.03)',
                    color: qtype === item.id ? '#FFF' : '#94A3B8',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease',
                    textAlign: 'center',
                    boxShadow: qtype === item.id ? '0 0 12px rgba(99, 102, 241, 0.2)' : 'none'
                  }}
                >
                  <div style={{ fontWeight: 700, fontSize: '0.88rem' }}>{item.label}</div>
                  <div style={{ fontSize: '0.72rem', color: qtype === item.id ? '#A5B4FC' : '#64748B' }}>{item.desc}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Difficulty Visual Options */}
          <div style={{ marginBottom: '18px' }}>
            <label className="form-label" style={{ marginBottom: '8px' }}>Difficulty Level</label>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px' }}>
              {[
                { id: 'easy', label: 'Easy', color: '#10B981' },
                { id: 'medium', label: 'Medium', color: '#F59E0B' },
                { id: 'hard', label: 'Hard', color: '#F43F5E' }
              ].map((item) => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => setDifficulty(item.id)}
                  style={{
                    padding: '10px 8px',
                    borderRadius: '12px',
                    border: `1px solid ${difficulty === item.id ? item.color : 'rgba(255, 255, 255, 0.08)'}`,
                    background: difficulty === item.id ? `${item.color}22` : 'rgba(255, 255, 255, 0.03)',
                    color: difficulty === item.id ? '#FFF' : '#94A3B8',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease',
                    textAlign: 'center'
                  }}
                >
                  <div style={{ fontWeight: 700, fontSize: '0.88rem', color: difficulty === item.id ? item.color : '#94A3B8' }}>
                    {item.label}
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Subject input */}
          <div className="form-group" style={{ marginBottom: '20px' }}>
            <label className="form-label">Subject Tag / Topic</label>
            <input
              type="text"
              className="input-field"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              placeholder="e.g. Physics, Biology, World History"
            />
          </div>

          {/* Question Count Selector */}
          <div style={{ marginBottom: '24px' }}>
            <label className="form-label" style={{ display: 'block', marginBottom: '8px' }}>
              Number of Questions to Generate
            </label>
            
            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '14px' }}>
              {[5, 10, 15, 20, 25, 30].map((preset) => (
                <button
                  key={preset}
                  type="button"
                  onClick={() => setNumQuestions(preset)}
                  style={{
                    padding: '6px 14px',
                    borderRadius: '20px',
                    fontSize: '0.82rem',
                    fontWeight: 700,
                    border: '1px solid',
                    borderColor: numQuestions === preset ? '#6366F1' : 'rgba(255, 255, 255, 0.12)',
                    background: numQuestions === preset ? 'rgba(99, 102, 241, 0.22)' : 'rgba(255, 255, 255, 0.04)',
                    color: numQuestions === preset ? '#818CF8' : '#94A3B8',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease'
                  }}
                >
                  {preset} Qs
                </button>
              ))}
            </div>

            {/* Stepper counter */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <button
                type="button"
                className="btn-secondary"
                style={{ padding: '8px 14px', borderRadius: '10px' }}
                onClick={() => setNumQuestions(Math.max(1, numQuestions - 1))}
              >
                <Minus size={16} />
              </button>
              <input
                type="number"
                min="1"
                max="50"
                className="input-field"
                style={{ width: '80px', textAlign: 'center', fontWeight: 800, fontSize: '1.1rem' }}
                value={numQuestions}
                onChange={(e) => setNumQuestions(Math.min(50, Math.max(1, parseInt(e.target.value) || 1)))}
              />
              <button
                type="button"
                className="btn-secondary"
                style={{ padding: '8px 14px', borderRadius: '10px' }}
                onClick={() => setNumQuestions(Math.min(50, numQuestions + 1))}
              >
                <Plus size={16} />
              </button>
              <span style={{ fontSize: '0.82rem', color: '#94A3B8' }}>Questions (Max 50)</span>
            </div>
          </div>

          <button
            onClick={handleGenerate}
            disabled={loading || !selectedFile}
            className="btn-primary"
            style={{ width: '100%', justifyContent: 'center', padding: '15px', borderRadius: '14px', fontSize: '1rem' }}
          >
            {loading ? (
              <>
                <span className="spinner">✨</span> Vision AI Extracting & Generating ({numQuestions} Qs)...
              </>
            ) : (
              <>
                <Sparkles size={20} /> Generate {numQuestions} Questions Bank
              </>
            )}
          </button>
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <div style={{
          background: 'rgba(244, 63, 94, 0.12)',
          border: '1px solid rgba(244, 63, 94, 0.3)',
          color: '#FB7185',
          padding: '16px 20px',
          borderRadius: '14px',
          marginBottom: '28px',
          display: 'flex',
          alignItems: 'center',
          gap: '12px'
        }}>
          <AlertCircle size={20} style={{ flexShrink: 0 }} />
          <span>{error}</span>
        </div>
      )}

      {/* Generated Questions Section */}
      {questions.length > 0 && (
        <div>
          {/* Header Action Bar */}
          <div className="glass-panel" style={{
            padding: '20px 28px',
            marginBottom: '24px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '16px',
            background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.85) 0%, rgba(30, 41, 59, 0.85) 100%)'
          }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '4px' }}>
                <span className="badge badge-emerald"><CheckCircle size={12} /> Generation Complete</span>
                <span className="badge badge-indigo">{questions.length} Questions</span>
              </div>
              <h3 style={{ fontSize: '1.4rem', fontWeight: 800 }}>{quizTitle}</h3>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <button
                onClick={handleSaveToLibrary}
                className={saveSuccess ? 'btn-secondary' : 'btn-primary'}
                disabled={saveSuccess}
                style={{ background: saveSuccess ? 'rgba(16, 185, 129, 0.2)' : undefined }}
              >
                {saveSuccess ? <CheckCircle size={16} color="#10B981" /> : <Save size={16} />}
                {saveSuccess ? 'Saved to Library!' : 'Save Quiz Bank'}
              </button>

              {saveSuccess && (
                <button
                  onClick={onNavigateToLibrary}
                  className="btn-secondary"
                  style={{ borderColor: '#6366F1', color: '#818CF8' }}
                >
                  <BookOpen size={16} /> View in Library
                </button>
              )}


              <button
                onClick={() => setIsExportOpen(true)}
                className="btn-primary"
                style={{ background: 'linear-gradient(135deg, #10B981 0%, #059669 100%)' }}
              >
                <Download size={16} /> Export Package (.docx)
              </button>
            </div>
          </div>

          {/* Question Cards List */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {questions.map((q, idx) => (
              <QuestionCard
                key={idx}
                index={idx + 1}
                question={q}
                onUpdate={(updated) => handleUpdateQuestion(idx, updated)}
                onDelete={() => handleDeleteQuestion(idx)}
              />
            ))}
          </div>
        </div>
      )}

      {/* Export Modal */}
      <ExportModal
        isOpen={isExportOpen}
        onClose={() => setIsExportOpen(false)}
        quizTitle={quizTitle}
        quizId={savedQuizId}
        questions={questions}
      />
    </div>
  );
};
