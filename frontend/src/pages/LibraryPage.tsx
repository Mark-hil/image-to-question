import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import type { QuizData, QuestionData } from '../services/api';
import { ExportModal } from '../components/ExportModal';
import { QuestionCard } from '../components/QuestionCard';
import { Library, Search, Download, Trash2, BookOpen, Calendar, Lock, Eye, X, CheckSquare, Square, FileArchive } from 'lucide-react';

interface LibraryPageProps {
  token: string | null;
  onOpenAuth: () => void;
}

export const LibraryPage: React.FC<LibraryPageProps> = ({ token, onOpenAuth }) => {
  const [quizzes, setQuizzes] = useState<QuizData[]>([]);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState('');
  const [selectedQuiz, setSelectedQuiz] = useState<QuizData | null>(null);
  const [viewingQuiz, setViewingQuiz] = useState<QuizData | null>(null);
  const [isExportOpen, setIsExportOpen] = useState(false);

  // Multi-select bulk selection state
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [bulkExportFormat, setBulkExportFormat] = useState<'csv' | 'docx' | 'qti' | 'text'>('csv');
  const [isBulkExporting, setIsBulkExporting] = useState(false);
  const [isBulkDeleting, setIsBulkDeleting] = useState(false);

  useEffect(() => {
    if (token) {
      fetchQuizzes();
    }
  }, [token]);

  const fetchQuizzes = async () => {
    if (!token) return;
    setLoading(true);
    try {
      const data = await api.listQuizzes(token);
      setQuizzes(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const toggleSelectQuiz = (id: string, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  };

  const toggleSelectAll = () => {
    if (selectedIds.length === filtered.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(filtered.map((q) => q.id));
    }
  };

  const handleDelete = async (quizId: string) => {
    if (!token || !confirm('Are you sure you want to delete this quiz bank?')) return;
    try {
      await api.deleteQuiz(token, quizId);
      setQuizzes(quizzes.filter((q) => q.id !== quizId));
      setSelectedIds(selectedIds.filter((id) => id !== quizId));
      if (viewingQuiz?.id === quizId) {
        setViewingQuiz(null);
      }
    } catch (err) {
      alert('Failed to delete quiz.');
    }
  };

  const handleBulkDelete = async () => {
    if (!token || selectedIds.length === 0) return;
    if (!confirm(`Are you sure you want to delete ${selectedIds.length} quiz bank(s)?`)) return;

    setIsBulkDeleting(true);
    try {
      await api.bulkDeleteQuizzes(token, selectedIds);
      setQuizzes(quizzes.filter((q) => !selectedIds.includes(q.id)));
      setSelectedIds([]);
    } catch (err: any) {
      alert(err.message || 'Failed to bulk delete quizzes');
    } finally {
      setIsBulkDeleting(false);
    }
  };

  const handleBulkExport = async () => {
    if (!token || selectedIds.length === 0) return;

    setIsBulkExporting(true);
    try {
      await api.bulkExportQuizzes(token, selectedIds, bulkExportFormat);
    } catch (err: any) {
      alert(err.message || 'Failed to bulk export quizzes');
    } finally {
      setIsBulkExporting(false);
    }
  };

  const handleUpdateQuestion = async (qIdx: number, updatedQ: QuestionData) => {
    if (!viewingQuiz || !token) return;
    const updatedQuestions = [...(viewingQuiz.questions || [])];
    updatedQuestions[qIdx] = updatedQ;

    setViewingQuiz({
      ...viewingQuiz,
      questions: updatedQuestions,
    });

    if (updatedQ.id) {
      try {
        await api.updateQuestion(token, viewingQuiz.id, String(updatedQ.id), {
          question_text: updatedQ.question_text || updatedQ.question,
          answer_text: updatedQ.answer_text || updatedQ.answer,
          choices: updatedQ.choices,
          rationale: updatedQ.rationale,
          difficulty: updatedQ.difficulty,
          blooms_level: updatedQ.blooms_level,
          class_id: updatedQ.class_id,
        });
      } catch (err) {
        console.error('Failed to save question edit to server:', err);
      }
    }
  };

  const handleDeleteQuestion = (qIdx: number) => {
    if (!viewingQuiz) return;
    const updatedQuestions = (viewingQuiz.questions || []).filter((_, idx) => idx !== qIdx);
    setViewingQuiz({
      ...viewingQuiz,
      questions: updatedQuestions,
      question_count: updatedQuestions.length,
    });
  };

  const filtered = quizzes.filter(
    (q) =>
      q.title.toLowerCase().includes(search.toLowerCase()) ||
      q.subject.toLowerCase().includes(search.toLowerCase()) ||
      (q.class_id && q.class_id.toLowerCase().includes(search.toLowerCase()))
  );

  if (!token) {
    return (
      <div style={{ width: '92%', maxWidth: '800px', margin: '60px auto', textAlign: 'center' }}>
        <div className="glass-panel" style={{ padding: '48px 32px' }}>
          <div style={{ padding: '20px', background: 'rgba(99, 102, 241, 0.15)', borderRadius: '50%', width: 'fit-content', margin: '0 auto 20px auto', color: '#818CF8' }}>
            <Lock size={40} />
          </div>
          <h2 style={{ fontSize: '1.8rem', fontWeight: 800, marginBottom: '12px' }}>
            Sign In to Access Your Quiz Library
          </h2>
          <p style={{ color: '#94A3B8', marginBottom: '28px', maxWidth: '480px', margin: '0 auto 28px auto' }}>
            Save, organize, and export your generated question banks anytime from any device.
          </p>
          <button className="btn-primary" onClick={onOpenAuth} style={{ padding: '14px 28px' }}>
            Sign In / Register Account
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="responsive-padding" style={{ width: '100%', maxWidth: '100%', padding: '24px 36px 80px 36px', position: 'relative' }}>
      
      {/* Header Bar */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h2 style={{ fontSize: '1.8rem', fontWeight: 800, display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Library color="#818CF8" /> My Saved Quiz Library
          </h2>
          <p style={{ color: '#94A3B8', fontSize: '0.9rem' }}>
            Manage quiz banks, select multiple items for bulk CSV / Word zip export, and edit questions inline.
          </p>
        </div>

        {/* Search & Select All Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {filtered.length > 0 && (
            <button
              onClick={toggleSelectAll}
              className="btn-secondary"
              style={{ padding: '8px 14px', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '6px' }}
            >
              {selectedIds.length === filtered.length ? <CheckSquare size={16} color="#10B981" /> : <Square size={16} />}
              {selectedIds.length === filtered.length ? 'Deselect All' : 'Select All'}
            </button>
          )}

          <div style={{ position: 'relative', width: '260px' }}>
            <Search size={16} color="#64748B" style={{ position: 'absolute', left: '12px', top: '12px' }} />
            <input
              type="text"
              className="input-field"
              placeholder="Search by title, class..."
              style={{ width: '100%', paddingLeft: '38px' }}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
        </div>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '60px', color: '#94A3B8' }}>
          <span className="spinner">✨</span> Loading your quiz library...
        </div>
      ) : filtered.length === 0 ? (
        <div className="glass-panel" style={{ padding: '48px', textAlign: 'center', color: '#94A3B8' }}>
          <BookOpen size={48} color="#64748B" style={{ marginBottom: '16px' }} />
          <h3>No Quiz Banks Found</h3>
          <p style={{ fontSize: '0.9rem', marginTop: '6px' }}>Generate a set of questions in the Studio and click "Save Quiz Bank".</p>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '20px' }}>
          {filtered.map((quiz) => {
            const isSelected = selectedIds.includes(quiz.id);
            return (
              <div
                key={quiz.id}
                className="glass-panel"
                style={{
                  padding: '24px',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  border: isSelected ? '1px solid #6366F1' : '1px solid rgba(255, 255, 255, 0.08)',
                  background: isSelected ? 'rgba(99, 102, 241, 0.08)' : undefined,
                  transition: 'all 0.2s ease',
                  position: 'relative'
                }}
              >
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                      <button
                        type="button"
                        onClick={(e) => toggleSelectQuiz(quiz.id, e)}
                        style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '2px', display: 'flex', alignItems: 'center' }}
                      >
                        {isSelected ? <CheckSquare size={20} color="#6366F1" /> : <Square size={20} color="#64748B" />}
                      </button>

                      <span className="badge badge-indigo">{quiz.subject || 'General'}</span>

                      {quiz.class_id && (
                        <span
                          className="badge"
                          style={{
                            background: 'rgba(236, 72, 153, 0.15)',
                            color: '#F472B6',
                            border: '1px solid rgba(236, 72, 153, 0.3)',
                            fontWeight: 700
                          }}
                        >
                          🏫 {quiz.class_id}
                        </span>
                      )}
                    </div>

                    <span className="badge badge-emerald">{quiz.question_count} Qs</span>
                  </div>

                  <h3 style={{ fontSize: '1.2rem', fontWeight: 700, marginBottom: '8px', lineHeight: 1.3, cursor: 'pointer' }} onClick={() => setViewingQuiz(quiz)}>
                    {quiz.title}
                  </h3>

                  {quiz.original_file_name && (
                    <div style={{ fontSize: '0.8rem', color: '#64748B', display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '16px' }}>
                      <BookOpen size={14} /> {quiz.original_file_name}
                    </div>
                  )}
                </div>

                <div>
                  <div style={{ fontSize: '0.78rem', color: '#94A3B8', display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '16px' }}>
                    <Calendar size={14} /> Created: {new Date(quiz.created_at).toLocaleDateString()}
                  </div>

                  <div style={{ display: 'flex', gap: '8px', borderTop: '1px solid rgba(255, 255, 255, 0.08)', paddingTop: '16px' }}>
                    <button
                      onClick={() => setViewingQuiz(quiz)}
                      className="btn-primary"
                      style={{ flex: 1, padding: '8px 12px', fontSize: '0.85rem', justifyContent: 'center' }}
                    >
                      <Eye size={14} /> View Quiz
                    </button>

                    <button
                      onClick={() => { setSelectedQuiz(quiz); setIsExportOpen(true); }}
                      className="btn-secondary"
                      style={{ padding: '8px 12px', fontSize: '0.85rem' }}
                      title="Export Quiz"
                    >
                      <Download size={14} /> Export
                    </button>

                    <button
                      onClick={() => handleDelete(quiz.id)}
                      className="btn-danger"
                      style={{ padding: '8px 12px' }}
                      title="Delete Quiz"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Sticky Floating Bulk Actions Bar */}
      {selectedIds.length > 0 && (
        <div style={{
          position: 'fixed',
          bottom: '24px',
          left: '50%',
          transform: 'translateX(-50%)',
          background: 'rgba(15, 23, 42, 0.92)',
          backdropFilter: 'blur(16px)',
          border: '1px solid rgba(99, 102, 241, 0.4)',
          borderRadius: '16px',
          padding: '14px 24px',
          display: 'flex',
          alignItems: 'center',
          gap: '20px',
          zIndex: 1000,
          boxShadow: '0 12px 40px rgba(0, 0, 0, 0.6)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{
              background: '#6366F1',
              color: '#FFF',
              fontSize: '0.82rem',
              fontWeight: 800,
              padding: '4px 10px',
              borderRadius: '20px'
            }}>
              {selectedIds.length} Selected
            </span>
            <span style={{ fontSize: '0.9rem', color: '#CBD5E1', fontWeight: 600 }}>Bulk Quiz Actions:</span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            {/* Format Selector */}
            <select
              className="input-field"
              style={{ padding: '6px 12px', fontSize: '0.85rem', width: 'auto', background: 'rgba(255, 255, 255, 0.08)' }}
              value={bulkExportFormat}
              onChange={(e) => setBulkExportFormat(e.target.value as any)}
            >
              <option value="csv">CSV Spreadsheets (.zip)</option>
              <option value="docx">Word Documents (.zip)</option>
              <option value="qti">Canvas QTI Packages (.zip)</option>
              <option value="text">Printable Text Files (.zip)</option>
            </select>

            <button
              onClick={handleBulkExport}
              disabled={isBulkExporting}
              className="btn-primary"
              style={{ padding: '8px 16px', fontSize: '0.85rem', background: 'linear-gradient(135deg, #059669 0%, #10B981 100%)' }}
            >
              <FileArchive size={15} /> {isBulkExporting ? 'Packaging Zip...' : 'Bulk Export Zip'}
            </button>

            <button
              onClick={handleBulkDelete}
              disabled={isBulkDeleting}
              className="btn-danger"
              style={{ padding: '8px 16px', fontSize: '0.85rem' }}
            >
              <Trash2 size={15} /> {isBulkDeleting ? 'Deleting...' : 'Delete Selected'}
            </button>

            <button
              onClick={() => setSelectedIds([])}
              style={{ background: 'none', border: 'none', color: '#94A3B8', cursor: 'pointer', padding: '4px', marginLeft: '6px' }}
              title="Clear selection"
            >
              <X size={18} />
            </button>
          </div>
        </div>
      )}

      {/* Quiz Detail View Modal */}
      {viewingQuiz && (
        <div style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(0, 0, 0, 0.82)',
          backdropFilter: 'blur(10px)',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          zIndex: 1100,
          padding: '24px'
        }}>
          <div className="glass-panel" style={{
            width: '100%',
            maxWidth: '900px',
            maxHeight: '90vh',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
            padding: '0',
            position: 'relative'
          }}>
            {/* Modal Header */}
            <div style={{
              padding: '20px 28px',
              borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              background: 'rgba(15, 23, 42, 0.6)'
            }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '4px' }}>
                  <span className="badge badge-indigo">{viewingQuiz.subject || 'General'}</span>
                  {viewingQuiz.class_id && (
                    <span className="badge" style={{ background: 'rgba(236, 72, 153, 0.15)', color: '#F472B6', border: '1px solid rgba(236, 72, 153, 0.3)' }}>
                      🏫 {viewingQuiz.class_id}
                    </span>
                  )}
                  <span className="badge badge-emerald">{viewingQuiz.questions?.length || viewingQuiz.question_count} Questions</span>
                </div>
                <h3 style={{ fontSize: '1.4rem', fontWeight: 800 }}>{viewingQuiz.title}</h3>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <button
                  onClick={() => { setSelectedQuiz(viewingQuiz); setIsExportOpen(true); }}
                  className="btn-primary"
                  style={{ padding: '8px 16px', fontSize: '0.88rem' }}
                >
                  <Download size={15} /> Export Quiz
                </button>

                <button
                  onClick={() => setViewingQuiz(null)}
                  style={{ background: 'none', border: 'none', color: '#94A3B8', cursor: 'pointer', padding: '4px' }}
                >
                  <X size={24} />
                </button>
              </div>
            </div>

            {/* Questions Scrollable Body */}
            <div style={{
              flex: 1,
              overflowY: 'auto',
              padding: '28px',
              display: 'flex',
              flexDirection: 'column',
              gap: '18px'
            }}>
              {viewingQuiz.questions && viewingQuiz.questions.length > 0 ? (
                viewingQuiz.questions.map((q, idx) => (
                  <QuestionCard
                    key={q.id || idx}
                    index={idx + 1}
                    question={q}
                    onUpdate={(updated) => handleUpdateQuestion(idx, updated)}
                    onDelete={() => handleDeleteQuestion(idx)}
                  />
                ))
              ) : (
                <div style={{ textAlign: 'center', padding: '40px', color: '#94A3B8' }}>
                  No question details available for this bank.
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Export Modal */}
      {selectedQuiz && (
        <ExportModal
          isOpen={isExportOpen}
          onClose={() => setIsExportOpen(false)}
          quizTitle={selectedQuiz.title}
          quizId={selectedQuiz.id}
          questions={selectedQuiz.questions || []}
        />
      )}
    </div>
  );
};
