import React, { useState } from 'react';
import { Dropzone } from '../components/Dropzone';
import { QuestionCard } from '../components/QuestionCard';
import { ExportModal } from '../components/ExportModal';
import { api } from '../services/api';
import type { QuestionData } from '../services/api';
import { Sparkles, Sliders, Save, Download, AlertCircle, BookOpen, Plus, Minus, CheckCircle, Check, Loader2, Zap, Brain, Target, Layers, Lock, GraduationCap } from 'lucide-react';

interface GeneratorPageProps {
  user: any;
  token: string | null;
  onOpenAuth: () => void;
  onNavigateToLibrary: () => void;
  onNavigateToPricing?: () => void;
  onRefreshUser?: () => void;
}

export const GeneratorPage: React.FC<GeneratorPageProps> = ({
  user,
  token,
  onOpenAuth,
  onNavigateToLibrary,
  onNavigateToPricing,
  onRefreshUser
}) => {

  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [selectedQtypes, setSelectedQtypes] = useState<string[]>(['mcq']);
  const [selectedDifficulties, setSelectedDifficulties] = useState<string[]>(['medium']);
  const [selectedBlooms, setSelectedBlooms] = useState<string[]>(['all']);

  // Multi-selection handlers
  const toggleQtype = (id: string) => {
    if (selectedQtypes.includes(id)) {
      if (selectedQtypes.length > 1) {
        setSelectedQtypes(selectedQtypes.filter(t => t !== id));
      }
    } else {
      setSelectedQtypes([...selectedQtypes, id]);
    }
  };

  const selectAllQtypes = () => {
    if (selectedQtypes.length === 3) {
      setSelectedQtypes(['mcq']);
    } else {
      setSelectedQtypes(['mcq', 'true_false', 'short_answer']);
    }
  };

  const toggleDifficulty = (id: string) => {
    if (selectedDifficulties.includes(id)) {
      if (selectedDifficulties.length > 1) {
        setSelectedDifficulties(selectedDifficulties.filter(d => d !== id));
      }
    } else {
      setSelectedDifficulties([...selectedDifficulties, id]);
    }
  };

  const toggleBlooms = (id: string) => {
    if (id === 'all') {
      setSelectedBlooms(['all']);
      return;
    }
    const filtered = selectedBlooms.filter(b => b.toLowerCase() !== 'all');
    if (filtered.includes(id)) {
      const next = filtered.filter(b => b !== id);
      setSelectedBlooms(next.length === 0 ? ['all'] : next);
    } else {
      const next = [...filtered, id];
      if (next.length === 6) {
        setSelectedBlooms(['all']);
      } else {
        setSelectedBlooms(next);
      }
    }
  };

  const qtypeParam = selectedQtypes.join(',');
  const diffParam = selectedDifficulties.join(',');
  const bloomsParam = selectedBlooms.includes('all') ? 'all' : selectedBlooms.join(',');
  const [mode, setMode] = useState<'exam' | 'practice'>('exam');
  const [numQuestions, setNumQuestions] = useState<number>(10);
  const [subject, setSubject] = useState<string>('Biology');
  const [classId, setClassId] = useState<string>('Grade 10');
  const [quizTitle, setQuizTitle] = useState<string>('My Quiz Bank');
  const [pageRange, setPageRange] = useState<string>('');
  const [detectedChapters, setDetectedChapters] = useState<Array<{ title: string; range: string; start_page: number; end_page: number }>>([]);
  const [pdfTotalPages, setPdfTotalPages] = useState<number>(0);
  const [inspectingPdf, setInspectingPdf] = useState<boolean>(false);
  const [selectedChapterRange, setSelectedChapterRange] = useState<string | null>(null);
  const [useAsyncPipeline, setUseAsyncPipeline] = useState<boolean>(true);
  const [guestUsesCount, setGuestUsesCount] = useState<number>(() => {
    const stored = localStorage.getItem('qgen_guest_uses');
    return stored ? parseInt(stored, 10) || 0 : 0;
  });

  const maxAllowedQuestions = user ? (user.max_questions_per_quiz || 20) : 5;
  const totalLimit = user?.monthly_limit || 6;
  const usedCount = user?.monthly_generations_used || 0;
  const remainingCount = user?.generations_remaining !== undefined ? user.generations_remaining : Math.max(0, totalLimit - usedCount);

  const totalQuestionsLimit = user?.monthly_questions_limit || (user?.tier === 'pro' ? 1000 : 120);
  const questionsUsedCount = user?.monthly_questions_generated || 0;
  const questionsRemaining = user?.total_questions_remaining !== undefined ? user.total_questions_remaining : Math.max(0, totalQuestionsLimit - questionsUsedCount);
  const isQuestionLimitDepleted = !!user && questionsRemaining <= 0;
  const isQuotaDepleted = !!user && (remainingCount <= 0 || isQuestionLimitDepleted);
  const isNearLimit = !!user && !isQuotaDepleted && (remainingCount <= 2 || questionsRemaining <= 20);
  const usagePct = Math.min(100, Math.round((usedCount / totalLimit) * 100));

  const [limitHitNotice, setLimitHitNotice] = useState<string | null>(null);

  React.useEffect(() => {
    if (!user && numQuestions > 5) {
      setNumQuestions(5);
    } else if (user && numQuestions > maxAllowedQuestions) {
      setNumQuestions(maxAllowedQuestions);
    }
  }, [user, maxAllowedQuestions]);

  const incrementGuestUses = () => {
    if (!user) {
      const next = guestUsesCount + 1;
      setGuestUsesCount(next);
      localStorage.setItem('qgen_guest_uses', next.toString());
    }
  };

  const handleFilesChange = async (files: File[]) => {
    setSelectedFiles(files);
    setDetectedChapters([]);
    setPdfTotalPages(0);
    setSelectedChapterRange(null);

    const docFile = files.find(f => {
      const name = f.name.toLowerCase();
      return name.endsWith('.pdf') || name.endsWith('.pptx') || name.endsWith('.ppt');
    });

    if (docFile) {
      setInspectingPdf(true);
      try {
        const res = await api.inspectPdf(docFile);
        if (res) {
          setPdfTotalPages(res.total_pages || 0);
          if (res.chapters && res.chapters.length > 0) {
            setDetectedChapters(res.chapters);
          }
        }
      } catch (e) {
        console.warn('Document TOC inspection note:', e);
      } finally {
        setInspectingPdf(false);
      }
    }
  };

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [questions, setQuestions] = useState<QuestionData[]>([]);

  // Generation Progress Bar State
  const [progressModalOpen, setProgressModalOpen] = useState<boolean>(false);
  const [progressPct, setProgressPct] = useState<number>(0);
  const [progressStage, setProgressStage] = useState<string>('Initializing pipeline...');
  const [progressStatus, setProgressStatus] = useState<string>('processing');

  const [savedQuizId, setSavedQuizId] = useState<string | undefined>(undefined);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [isExportOpen, setIsExportOpen] = useState(false);

  const pollTaskStatus = async (taskId: string) => {
    let completed = false;
    while (!completed) {
      try {
        await new Promise((resolve) => setTimeout(resolve, 1100));
        const res = await api.getTaskStatus(taskId);
        setProgressPct(res.progress || 0);
        setProgressStage(res.stage || 'Processing document extractions...');
        setProgressStatus(res.status);

        if (res.status === 'completed') {
          completed = true;
          if (res.questions && res.questions.length > 0) {
            const formatted = res.questions.map(q => ({ ...q, class_id: q.class_id || classId }));
            setQuestions(formatted);
            if (selectedFiles.length > 0) {
              setQuizTitle(selectedFiles[0].name.replace(/\.[^/.]+$/, "") + " Quiz");
            }
          }
          if (res.limit_hit_warning) {
            setLimitHitNotice(res.limit_hit_warning);
          }
          incrementGuestUses();
          onRefreshUser?.();
          setTimeout(() => {
            setProgressModalOpen(false);
            setLoading(false);
          }, 600);
        } else if (res.status === 'failed') {
          completed = true;
          setError(res.error || 'Async generation task failed.');
          setProgressModalOpen(false);
          setLoading(false);
        }
      } catch (err: any) {
        completed = true;
        setError(err.message || 'Error checking task status.');
        setProgressModalOpen(false);
        setLoading(false);
      }
    }
  };

  const handleGenerate = async () => {
    if (!user && guestUsesCount >= 3) {
      setError('You have reached your 3 free guest generation chances! Please sign in or create a free account to continue.');
      onOpenAuth();
      return;
    }

    if (selectedFiles.length === 0) {
      setError('Please select at least one document or image file.');
      return;
    }

    const effectiveNumQuestions = user ? numQuestions : Math.min(5, numQuestions);

    setLoading(true);
    setError(null);
    setProgressModalOpen(true);
    setProgressPct(5);
    setProgressStatus('processing');

    if (useAsyncPipeline) {
      setProgressStage('Queueing documents into background pipeline...');

      try {
        const result = await api.generateAsync(
          selectedFiles,
          qtypeParam,
          diffParam,
          effectiveNumQuestions,
          subject,
          undefined,
          bloomsParam,
          pageRange,
          mode
        );
        pollTaskStatus(result.task_id);
      } catch (err: any) {
        setError(err.message || 'Failed to start background question pipeline.');
        setProgressModalOpen(false);
        setLoading(false);
      }
    } else {
      // Synchronous flow with animated progress increments
      try {
        setProgressStage('Reading source documents & applying Groq Vision VLM...');
        setProgressPct(25);
        
        const progTimer1 = setTimeout(() => {
          setProgressPct(60);
          setProgressStage(`Generating questions with Bloom's Taxonomy: ${bloomsParam.toUpperCase()}...`);
        }, 1500);

        const progTimer2 = setTimeout(() => {
          setProgressPct(85);
          setProgressStage('Formatting JSON structure & answer rationale...');
        }, 3500);

        const generated = await api.uploadAndGenerate(
          selectedFiles,
          qtypeParam,
          diffParam,
          effectiveNumQuestions,
          subject,
          undefined,
          classId,
          bloomsParam,
          pageRange,
          mode
        );

        clearTimeout(progTimer1);
        clearTimeout(progTimer2);

        setProgressPct(100);
        setProgressStage('Generation Complete!');
        setProgressStatus('completed');

        const formatted = generated.map(q => ({ ...q, class_id: q.class_id || classId }));
        setQuestions(formatted);
        if (selectedFiles.length > 0) {
          setQuizTitle(selectedFiles[0].name.replace(/\.[^/.]+$/, "") + " Quiz");
        }
        if ((generated as any).limit_hit_warning) {
          setLimitHitNotice((generated as any).limit_hit_warning);
        }
        incrementGuestUses();
        onRefreshUser?.();

        setTimeout(() => {
          setProgressModalOpen(false);
          setLoading(false);
        }, 600);
      } catch (err: any) {
        setError(err.message || 'Error generating questions.');
        setProgressModalOpen(false);
        setLoading(false);
      }
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
      const sourceName = selectedFiles.map(f => f.name).join(', ');
      const saved = await api.saveQuiz(token, quizTitle, subject, sourceName, questions, classId);
      setSavedQuizId(saved.id);
      setSaveSuccess(true);
    } catch (err: any) {
      setError(err.message || 'Failed to save quiz bank.');
    }
  };

  const bloomsLevelsList = [
    { id: 'all', label: 'All Levels', desc: 'Balanced Mix', color: '#818CF8' },
    { id: 'Remember', label: 'Remember', desc: 'Recall facts', color: '#93C5FD' },
    { id: 'Understand', label: 'Understand', desc: 'Explain ideas', color: '#60A5FA' },
    { id: 'Apply', label: 'Apply', desc: 'Use info', color: '#34D399' },
    { id: 'Analyze', label: 'Analyze', desc: 'Draw connections', color: '#FBBF24' },
    { id: 'Evaluate', label: 'Evaluate', desc: 'Justify stance', color: '#F97316' },
    { id: 'Create', label: 'Create', desc: 'Produce original work', color: '#F43F5E' }
  ];

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
          <span className="badge badge-purple"><Layers size={12} /> Multi-Document Batch Processing</span>
          <span className="badge badge-emerald"><Target size={12} /> Granular Bloom's Taxonomy</span>
          {!user ? (
            <span className="badge" style={{ background: guestUsesCount >= 3 ? 'rgba(239, 68, 68, 0.2)' : 'rgba(245, 158, 11, 0.2)', color: guestUsesCount >= 3 ? '#F87171' : '#FBBF24', border: '1px solid rgba(245, 158, 11, 0.4)' }}>
              <Target size={12} /> Guest Trial: {guestUsesCount}/3 Used ({Math.max(0, 3 - guestUsesCount)} left)
            </span>
          ) : user.tier === 'pro' ? (
            <span className="badge badge-emerald"><Zap size={12} /> Pro Tier: 100 Quizzes / Month</span>
          ) : (
            <span className="badge badge-indigo"><Zap size={12} /> Free Tier: {remainingCount} of {totalLimit} Quizzes Left</span>
          )}
        </div>
        <h2 style={{ fontSize: '2.3rem', fontWeight: 800, marginBottom: '10px' }} className="text-gradient">
          Worksheet & Textbook <span className="text-gradient-indigo">AI Question Studio</span>
        </h2>
        <p style={{ color: '#94A3B8', maxWidth: '720px', fontSize: '1rem', lineHeight: 1.6 }}>
          Upload multiple textbook pages or PDF documents simultaneously. Tailor targeted cognitive levels with Bloom's Taxonomy for MS Word (.docx) or Canvas LMS package exports.
        </p>
      </div>

      {/* Limit Hit & Quota Exhaustion Alert */}
      {limitHitNotice && (
        <div style={{
          background: 'linear-gradient(135deg, rgba(245, 158, 11, 0.16) 0%, rgba(99, 102, 241, 0.14) 100%)',
          border: '1px solid rgba(245, 158, 11, 0.4)',
          borderRadius: '14px',
          padding: '14px 20px',
          marginBottom: '24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '14px',
          boxShadow: '0 4px 15px rgba(245, 158, 11, 0.1)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <Zap size={20} color="#FBBF24" />
            <div>
              <div style={{ fontWeight: 800, color: '#FCD34D', fontSize: '0.9rem' }}>Generation Limit Notice</div>
              <div style={{ color: '#E2E8F0', fontSize: '0.84rem', marginTop: '2px' }}>{limitHitNotice}</div>
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            {onNavigateToPricing && (
              <button
                type="button"
                onClick={onNavigateToPricing}
                className="btn-primary"
                style={{ padding: '6px 14px', fontSize: '0.8rem', borderRadius: '8px', whiteSpace: 'nowrap' }}
              >
                Upgrade Plan
              </button>
            )}
            <button
              type="button"
              onClick={() => setLimitHitNotice(null)}
              style={{ background: 'none', border: 'none', color: '#94A3B8', cursor: 'pointer', fontSize: '1.2rem', padding: '2px 6px' }}
              title="Dismiss"
            >
              ✕
            </button>
          </div>
        </div>
      )}

      {/* Upload & Controls Grid */}
      <div className="responsive-grid-2" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '28px', marginBottom: '36px' }}>

        {/* Left: Multi-Document Dropzone Panel */}
        <div className="glass-panel" style={{ padding: '28px' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '18px', display: 'flex', alignItems: 'center', gap: '10px' }}>
            <BookOpen size={20} color="#818CF8" /> 1. Upload Source Documents
          </h3>
          <Dropzone selectedFiles={selectedFiles} onFilesChange={handleFilesChange} />
        </div>

        {/* Right: Options Panel */}
        <div className="glass-panel" style={{ padding: '28px' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '18px', display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Sliders size={20} color="#818CF8" /> 2. Question Options
          </h3>

          {/* Generation Mode Selector: Exam Assessment vs Study & Practice */}
          <div style={{ marginBottom: '20px' }}>
            <label className="form-label" style={{ marginBottom: '8px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <GraduationCap size={15} color={mode === 'exam' ? '#818CF8' : '#34D399'} /> Generation Mode
              </span>
              <span style={{ fontSize: '0.74rem', color: mode === 'exam' ? '#A5B4FC' : '#6EE7B7', fontWeight: 600 }}>
                {mode === 'exam' ? 'Educator Summative Assessment' : 'Learner Formative Practice'}
              </span>
            </label>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
              <button
                type="button"
                onClick={() => setMode('exam')}
                style={{
                  padding: '12px 14px',
                  borderRadius: '12px',
                  border: `1.5px solid ${mode === 'exam' ? '#6366F1' : 'rgba(255, 255, 255, 0.08)'}`,
                  background: mode === 'exam' ? 'rgba(99, 102, 241, 0.18)' : 'rgba(255, 255, 255, 0.02)',
                  color: mode === 'exam' ? '#FFF' : '#94A3B8',
                  cursor: 'pointer',
                  textAlign: 'left',
                  transition: 'all 0.2s ease',
                  boxShadow: mode === 'exam' ? '0 0 14px rgba(99, 102, 241, 0.25)' : 'none'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
                  <span style={{ fontWeight: 700, fontSize: '0.9rem', color: mode === 'exam' ? '#A5B4FC' : '#CBD5E1', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <GraduationCap size={16} color={mode === 'exam' ? '#818CF8' : '#94A3B8'} /> Exam Assessment
                  </span>
                  {mode === 'exam' && <Check size={14} strokeWidth={3} color="#818CF8" />}
                </div>
                <div style={{ fontSize: '0.72rem', color: mode === 'exam' ? '#E2E8F0' : '#64748B', lineHeight: '1.3' }}>
                  Rigorous tests with realistic distractors & scenario problems for tutors
                </div>
              </button>

              <button
                type="button"
                onClick={() => setMode('practice')}
                style={{
                  padding: '12px 14px',
                  borderRadius: '12px',
                  border: `1.5px solid ${mode === 'practice' ? '#10B981' : 'rgba(255, 255, 255, 0.08)'}`,
                  background: mode === 'practice' ? 'rgba(16, 185, 129, 0.16)' : 'rgba(255, 255, 255, 0.02)',
                  color: mode === 'practice' ? '#FFF' : '#94A3B8',
                  cursor: 'pointer',
                  textAlign: 'left',
                  transition: 'all 0.2s ease',
                  boxShadow: mode === 'practice' ? '0 0 14px rgba(16, 185, 129, 0.25)' : 'none'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
                  <span style={{ fontWeight: 700, fontSize: '0.9rem', color: mode === 'practice' ? '#6EE7B7' : '#CBD5E1', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <BookOpen size={16} color={mode === 'practice' ? '#10B981' : '#94A3B8'} /> Study & Practice
                  </span>
                  {mode === 'practice' && <Check size={14} strokeWidth={3} color="#10B981" />}
                </div>
                <div style={{ fontSize: '0.72rem', color: mode === 'practice' ? '#E2E8F0' : '#64748B', lineHeight: '1.3' }}>
                  Formative self-study with conceptual hints & revision rationales for learners
                </div>
              </button>
            </div>
          </div>

          {/* Question Type Visual Options with Multi-Selection */}
          <div style={{ marginBottom: '18px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
              <label className="form-label" style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span>Question Format</span>
                {selectedQtypes.length > 1 && (
                  <span className="badge badge-indigo" style={{ fontSize: '0.68rem', padding: '1px 7px' }}>
                    {selectedQtypes.length} formats selected
                  </span>
                )}
              </label>
              <button
                type="button"
                onClick={selectAllQtypes}
                style={{
                  background: selectedQtypes.length === 3 ? 'rgba(99, 102, 241, 0.22)' : 'rgba(255, 255, 255, 0.04)',
                  border: `1px solid ${selectedQtypes.length === 3 ? '#6366F1' : 'rgba(255, 255, 255, 0.12)'}`,
                  color: selectedQtypes.length === 3 ? '#A5B4FC' : '#94A3B8',
                  borderRadius: '8px',
                  padding: '3px 8px',
                  fontSize: '0.72rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  transition: 'all 0.15s ease'
                }}
                title="Toggle all question formats for a mixed quiz"
              >
                <Sparkles size={11} /> {selectedQtypes.length === 3 ? 'Reset to MCQ' : 'Select All / Mix'}
              </button>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px' }}>
              {[
                { id: 'mcq', label: 'MCQ', desc: 'Multiple Choice' },
                { id: 'true_false', label: 'True/False', desc: 'Binary' },
                { id: 'short_answer', label: 'Short Answer', desc: 'Open Text' }
              ].map((item) => {
                const isSelected = selectedQtypes.includes(item.id);
                return (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => toggleQtype(item.id)}
                    style={{
                      padding: '10px 8px',
                      borderRadius: '12px',
                      border: `1px solid ${isSelected ? '#6366F1' : 'rgba(255, 255, 255, 0.08)'}`,
                      background: isSelected ? 'rgba(99, 102, 241, 0.2)' : 'rgba(255, 255, 255, 0.03)',
                      color: isSelected ? '#FFF' : '#94A3B8',
                      cursor: 'pointer',
                      transition: 'all 0.2s ease',
                      textAlign: 'center',
                      boxShadow: isSelected ? '0 0 12px rgba(99, 102, 241, 0.25)' : 'none',
                      position: 'relative'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '5px', fontWeight: 700, fontSize: '0.88rem' }}>
                      {item.label}
                      {isSelected && <Check size={13} strokeWidth={3} color="#818CF8" />}
                    </div>
                    <div style={{ fontSize: '0.72rem', color: isSelected ? '#A5B4FC' : '#64748B' }}>{item.desc}</div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Difficulty Visual Options with Multi-Selection */}
          <div style={{ marginBottom: '18px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
              <label className="form-label" style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span>Difficulty Level</span>
                {selectedDifficulties.length > 1 && (
                  <span className="badge badge-amber" style={{ fontSize: '0.68rem', padding: '1px 7px' }}>
                    {selectedDifficulties.length} combined
                  </span>
                )}
              </label>
              <button
                type="button"
                onClick={() => {
                  if (selectedDifficulties.length === 3) {
                    setSelectedDifficulties(['medium']);
                  } else {
                    setSelectedDifficulties(['easy', 'medium', 'hard']);
                  }
                }}
                style={{
                  background: selectedDifficulties.length === 3 ? 'rgba(245, 158, 11, 0.2)' : 'rgba(255, 255, 255, 0.04)',
                  border: `1px solid ${selectedDifficulties.length === 3 ? '#F59E0B' : 'rgba(255, 255, 255, 0.12)'}`,
                  color: selectedDifficulties.length === 3 ? '#FCD34D' : '#94A3B8',
                  borderRadius: '8px',
                  padding: '3px 8px',
                  fontSize: '0.72rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  transition: 'all 0.15s ease'
                }}
                title="Combine multiple difficulty levels for progressive assessments"
              >
                {selectedDifficulties.length === 3 ? 'Reset to Medium' : 'Progressive (All 3)'}
              </button>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px' }}>
              {[
                { id: 'easy', label: 'Easy', color: '#10B981' },
                { id: 'medium', label: 'Medium', color: '#F59E0B' },
                { id: 'hard', label: 'Hard', color: '#F43F5E' }
              ].map((item) => {
                const isSelected = selectedDifficulties.includes(item.id);
                return (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => toggleDifficulty(item.id)}
                    style={{
                      padding: '10px 8px',
                      borderRadius: '12px',
                      border: `1px solid ${isSelected ? item.color : 'rgba(255, 255, 255, 0.08)'}`,
                      background: isSelected ? `${item.color}22` : 'rgba(255, 255, 255, 0.03)',
                      color: isSelected ? '#FFF' : '#94A3B8',
                      cursor: 'pointer',
                      transition: 'all 0.2s ease',
                      textAlign: 'center',
                      boxShadow: isSelected ? `0 0 10px ${item.color}33` : 'none'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '5px', fontWeight: 700, fontSize: '0.88rem', color: isSelected ? item.color : '#94A3B8' }}>
                      {item.label}
                      {isSelected && <Check size={13} strokeWidth={3} color={item.color} />}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Bloom's Taxonomy Filter Component with Multi-Selection */}
          <div style={{ marginBottom: '20px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
              <label className="form-label" style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Target size={14} color="#818CF8" /> Bloom's Taxonomy Cognitive Level
              </label>
              <span style={{ fontSize: '0.75rem', color: '#818CF8', fontWeight: 600 }}>
                {selectedBlooms.includes('all') ? 'Default: All Levels' : `${selectedBlooms.length} Level${selectedBlooms.length > 1 ? 's' : ''} Selected`}
              </span>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(105px, 1fr))', gap: '8px' }}>
              {bloomsLevelsList.map((item) => {
                const isSelected = item.id === 'all'
                  ? selectedBlooms.includes('all')
                  : selectedBlooms.includes(item.id);
                return (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => toggleBlooms(item.id)}
                    style={{
                      padding: '8px 6px',
                      borderRadius: '10px',
                      border: `1px solid ${isSelected ? item.color : 'rgba(255, 255, 255, 0.08)'}`,
                      background: isSelected ? `${item.color}25` : 'rgba(255, 255, 255, 0.02)',
                      color: isSelected ? '#FFF' : '#94A3B8',
                      cursor: 'pointer',
                      transition: 'all 0.2s ease',
                      textAlign: 'center',
                      boxShadow: isSelected ? `0 0 8px ${item.color}33` : 'none'
                    }}
                    title={item.desc}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '4px', fontWeight: 700, fontSize: '0.8rem', color: isSelected ? item.color : '#CBD5E1' }}>
                      {item.label}
                      {isSelected && <Check size={11} strokeWidth={3} color={item.color} />}
                    </div>
                    <div style={{ fontSize: '0.68rem', color: isSelected ? '#E2E8F0' : '#64748B', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {item.desc}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Subject, Class & PDF Page Range inputs */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1.2fr', gap: '14px', marginBottom: '20px' }}>
            <div className="form-group">
              <label className="form-label">Subject Tag / Topic</label>
              <input
                type="text"
                className="input-field"
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                placeholder="e.g. Physics, Biology"
              />
            </div>
            <div className="form-group">
              <label className="form-label">Class Tag / Grade</label>
              <input
                type="text"
                className="input-field"
                value={classId}
                onChange={(e) => setClassId(e.target.value)}
                placeholder="e.g. Grade 10, Class 5A"
              />
            </div>
            <div className="form-group">
              <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <BookOpen size={14} color="#818CF8" /> Page / Chapter Range
              </label>
              <input
                type="text"
                className="input-field"
                value={pageRange}
                onChange={(e) => {
                  setPageRange(e.target.value);
                  setSelectedChapterRange(null);
                }}
                placeholder="e.g. 8-20, 15, or blank for all"
                style={{
                  borderColor: pageRange ? '#6366F1' : undefined,
                  background: pageRange ? 'rgba(99, 102, 241, 0.08)' : undefined
                }}
              />
            </div>
          </div>

          {/* Detected PDF Chapter Pills (Option C - Hybrid TOC Extraction) */}
          {inspectingPdf && (
            <div style={{ marginBottom: '16px', fontSize: '0.8rem', color: '#818CF8', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Loader2 size={14} className="animate-spin" /> Auto-detecting PDF Table of Contents chapters...
            </div>
          )}

          {/* Detected PDF Chapter Pills or Quick Page Presets */}
          {detectedChapters.length > 0 ? (
            <div style={{ marginBottom: '20px', padding: '12px 14px', borderRadius: '12px', background: 'rgba(99, 102, 241, 0.08)', border: '1px solid rgba(99, 102, 241, 0.2)' }}>
              <div style={{ fontSize: '0.8rem', fontWeight: 700, color: '#A5B4FC', marginBottom: '8px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <BookOpen size={14} color="#818CF8" /> Auto-Detected Chapters ({detectedChapters.length})
                </span>
                <span style={{ fontSize: '0.72rem', color: '#64748B', fontWeight: 400 }}>Click pill to set page range</span>
              </div>
              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', maxHeight: '120px', overflowY: 'auto', paddingRight: '4px' }}>
                {detectedChapters.map((ch, idx) => {
                  const isSelected = selectedChapterRange === ch.range || pageRange === ch.range;
                  return (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => {
                        if (isSelected) {
                          setSelectedChapterRange(null);
                          setPageRange('');
                        } else {
                          setSelectedChapterRange(ch.range);
                          setPageRange(ch.range);
                        }
                      }}
                      style={{
                        padding: '5px 10px',
                        borderRadius: '8px',
                        fontSize: '0.78rem',
                        fontWeight: 600,
                        border: '1px solid',
                        borderColor: isSelected ? '#6366F1' : 'rgba(255, 255, 255, 0.12)',
                        background: isSelected ? 'rgba(99, 102, 241, 0.25)' : 'rgba(255, 255, 255, 0.04)',
                        color: isSelected ? '#FFF' : '#94A3B8',
                        cursor: 'pointer',
                        transition: 'all 0.15s ease',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px'
                      }}
                    >
                      <span>{ch.title}</span>
                      <span style={{ fontSize: '0.7rem', color: isSelected ? '#C7D2FE' : '#64748B', background: 'rgba(0,0,0,0.2)', padding: '2px 5px', borderRadius: '4px' }}>
                        p.{ch.range}
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>
          ) : pdfTotalPages > 0 ? (
            <div style={{ marginBottom: '20px', padding: '12px 14px', borderRadius: '12px', background: 'rgba(99, 102, 241, 0.08)', border: '1px solid rgba(99, 102, 241, 0.2)' }}>
              <div style={{ fontSize: '0.8rem', fontWeight: 700, color: '#A5B4FC', marginBottom: '8px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Layers size={14} color="#818CF8" /> Scanned / Image PDF ({pdfTotalPages} Total Pages)
                </span>
                <span style={{ fontSize: '0.72rem', color: '#64748B', fontWeight: 400 }}>Click preset pill or type range above</span>
              </div>
              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                {Array.from({ length: Math.min(12, Math.ceil(pdfTotalPages / 15)) }, (_, i) => {
                  const chunkSize = pdfTotalPages > 100 ? 20 : 10;
                  const startP = i * chunkSize + 1;
                  if (startP > pdfTotalPages) return null;
                  const endP = Math.min(pdfTotalPages, (i + 1) * chunkSize);
                  const rng = `${startP}-${endP}`;
                  const isSelected = pageRange === rng;
                  return (
                    <button
                      key={i}
                      type="button"
                      onClick={() => setPageRange(isSelected ? '' : rng)}
                      style={{
                        padding: '5px 11px',
                        borderRadius: '8px',
                        fontSize: '0.78rem',
                        fontWeight: 600,
                        border: '1px solid',
                        borderColor: isSelected ? '#6366F1' : 'rgba(255, 255, 255, 0.12)',
                        background: isSelected ? 'rgba(99, 102, 241, 0.25)' : 'rgba(255, 255, 255, 0.04)',
                        color: isSelected ? '#FFF' : '#94A3B8',
                        cursor: 'pointer',
                        transition: 'all 0.15s ease'
                      }}
                    >
                      Pages {rng}
                    </button>
                  );
                })}
              </div>
            </div>
          ) : null}

          {/* Question Count Selector */}
          <div style={{ marginBottom: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <label className="form-label" style={{ margin: 0 }}>
                Number of Questions to Generate
              </label>
              {!user ? (
                <span style={{ fontSize: '0.75rem', color: '#FBBF24', fontWeight: 600 }}>
                  Guest Max: 5 Qs (Sign up free for up to 20 Qs)
                </span>
              ) : (
                <span style={{ fontSize: '0.75rem', color: '#38BDF8', fontWeight: 600 }}>
                  {user.tier === 'pro' || user.tier === 'team' || user.tier === 'institution'
                    ? 'Pro Plan: up to 50 Qs'
                    : 'Free Plan: up to 20 Qs per quiz'}
                </span>
              )}
            </div>
            
            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '14px' }}>
              {[5, 10, 15, 20, 30, 50].map((preset) => {
                const isGuestLocked = !user && preset > 5;
                const isProLocked = !!user && preset > maxAllowedQuestions;
                const isLocked = isGuestLocked || isProLocked;
                const isSelected = numQuestions === preset;
                return (
                  <button
                    key={preset}
                    type="button"
                    onClick={() => {
                      if (isGuestLocked) {
                        onOpenAuth();
                      } else if (isProLocked && onNavigateToPricing) {
                        onNavigateToPricing();
                      } else if (!isLocked) {
                        setNumQuestions(preset);
                      }
                    }}
                    style={{
                      padding: '6px 14px',
                      borderRadius: '20px',
                      fontSize: '0.82rem',
                      fontWeight: 700,
                      border: '1px solid',
                      borderColor: isSelected ? '#6366F1' : 'rgba(255, 255, 255, 0.12)',
                      background: isSelected ? 'rgba(99, 102, 241, 0.22)' : 'rgba(255, 255, 255, 0.04)',
                      color: isSelected ? '#818CF8' : isLocked ? '#64748B' : '#94A3B8',
                      cursor: 'pointer',
                      transition: 'all 0.2s ease',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px',
                      opacity: isLocked ? 0.6 : 1
                    }}
                    title={
                      isGuestLocked
                        ? 'Sign in free to generate up to 30 questions'
                        : isProLocked
                        ? 'Upgrade to Pro for 50+ question banks'
                        : undefined
                    }
                  >
                    {preset} Qs {isLocked && <Lock size={10} color="#F87171" />}
                  </button>
                );
              })}
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
                max={maxAllowedQuestions}
                className="input-field"
                style={{ width: '80px', textAlign: 'center', fontWeight: 800, fontSize: '1.1rem' }}
                value={numQuestions}
                onChange={(e) => {
                  const val = parseInt(e.target.value) || 1;
                  setNumQuestions(Math.min(maxAllowedQuestions, Math.max(1, val)));
                }}
              />
              <button
                type="button"
                className="btn-secondary"
                style={{ padding: '8px 14px', borderRadius: '10px' }}
                onClick={() => setNumQuestions(Math.min(maxAllowedQuestions, numQuestions + 1))}
              >
                <Plus size={16} />
              </button>
              <span style={{ fontSize: '0.82rem', color: '#94A3B8' }}>
                Questions (Max {maxAllowedQuestions} for {user ? (user.tier === 'pro' ? 'Pro' : 'Free') : 'Guests'})
              </span>
            </div>
          </div>

          {/* Async Background Task Toggle */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '12px 16px',
            borderRadius: '14px',
            background: 'rgba(99, 102, 241, 0.08)',
            border: '1px solid rgba(99, 102, 241, 0.2)',
            marginBottom: '20px'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Zap size={18} color="#818CF8" />
              <div>
                <div style={{ fontSize: '0.88rem', fontWeight: 700, color: '#F8FAFC' }}>
                  Async Background Task Pipeline
                </div>
                <div style={{ fontSize: '0.76rem', color: '#94A3B8' }}>
                  Prevents timeouts for large PDFs & question batches
                </div>
              </div>
            </div>
            <label style={{ position: 'relative', display: 'inline-block', width: '44px', height: '24px', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={useAsyncPipeline}
                onChange={(e) => setUseAsyncPipeline(e.target.checked)}
                style={{ opacity: 0, width: 0, height: 0 }}
              />
              <span style={{
                position: 'absolute',
                top: 0, left: 0, right: 0, bottom: 0,
                backgroundColor: useAsyncPipeline ? '#6366F1' : '#334155',
                borderRadius: '24px',
                transition: '0.3s'
              }}>
                <span style={{
                  position: 'absolute',
                  content: '""',
                  height: '18px', width: '18px',
                  left: useAsyncPipeline ? '22px' : '3px',
                  bottom: '3px',
                  backgroundColor: '#FFF',
                  borderRadius: '50%',
                  transition: '0.3s',
                  boxShadow: '0 2px 5px rgba(0,0,0,0.3)'
                }} />
              </span>
            </label>
          </div>

          {/* Soft Limits & Visual Progress Card */}
          {user ? (
            <div style={{
              background: isQuotaDepleted
                ? 'rgba(239, 68, 68, 0.12)'
                : isNearLimit
                ? 'rgba(245, 158, 11, 0.12)'
                : 'rgba(255, 255, 255, 0.04)',
              border: '1px solid',
              borderColor: isQuotaDepleted
                ? 'rgba(239, 68, 68, 0.35)'
                : isNearLimit
                ? 'rgba(245, 158, 11, 0.35)'
                : 'rgba(255, 255, 255, 0.08)',
              padding: '14px 18px',
              borderRadius: '14px',
              marginBottom: '16px'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px', fontSize: '0.82rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 700, color: isQuotaDepleted ? '#F87171' : isNearLimit ? '#FBBF24' : '#38BDF8' }}>
                  <Zap size={14} />
                  <span>
                    {isQuotaDepleted
                      ? 'Monthly Generation Quota Depleted'
                      : isNearLimit
                      ? `Low Quota Warning: ${remainingCount} Quizzes (${questionsRemaining} Qs) Left`
                      : `${usedCount}/${totalLimit} Quizzes Used • ${questionsUsedCount}/${totalQuestionsLimit} Total Qs`}
                  </span>
                </div>
                <span style={{ color: '#94A3B8', fontSize: '0.75rem' }}>
                  {user.next_renewal_date ? `Renews ${user.next_renewal_date}` : '30-day cycle'}
                </span>
              </div>

              {/* Visual Progress Bar */}
              <div style={{
                height: '6px',
                background: 'rgba(255, 255, 255, 0.1)',
                borderRadius: '3px',
                overflow: 'hidden',
                marginBottom: '8px'
              }}>
                <div style={{
                  height: '100%',
                  width: `${usagePct}%`,
                  background: isQuotaDepleted
                    ? '#EF4444'
                    : isNearLimit
                    ? '#F59E0B'
                    : 'linear-gradient(90deg, #6366F1, #38BDF8)',
                  borderRadius: '3px',
                  transition: 'width 0.4s ease'
                }} />
              </div>

              {/* Explanatory Subtitle & Upgrade Action */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.75rem' }}>
                <span style={{ color: '#94A3B8' }}>
                  {isQuotaDepleted
                    ? `Auto-renews back to full quota in ${user.days_until_reset ?? 0} days.`
                    : `${remainingCount} quizzes left (${questionsRemaining} Qs allowance) • Max ${maxAllowedQuestions} Qs per quiz`}
                </span>
                {(isNearLimit || isQuotaDepleted) && onNavigateToPricing && (
                  <button
                    type="button"
                    onClick={onNavigateToPricing}
                    style={{
                      background: 'none',
                      border: 'none',
                      color: isQuotaDepleted ? '#F87171' : '#FBBF24',
                      fontWeight: 700,
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px',
                      padding: 0
                    }}
                  >
                    Upgrade to Pro <Zap size={12} />
                  </button>
                )}
              </div>
            </div>
          ) : (
            /* Guest Progress Card */
            <div style={{
              background: guestUsesCount >= 3 ? 'rgba(239, 68, 68, 0.12)' : 'rgba(245, 158, 11, 0.08)',
              border: '1px solid',
              borderColor: guestUsesCount >= 3 ? 'rgba(239, 68, 68, 0.35)' : 'rgba(245, 158, 11, 0.25)',
              padding: '14px 18px',
              borderRadius: '14px',
              marginBottom: '16px'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px', fontSize: '0.82rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 700, color: guestUsesCount >= 3 ? '#F87171' : '#FBBF24' }}>
                  <Sparkles size={14} />
                  <span>Guest Preview ({guestUsesCount}/3 Free Trials Used)</span>
                </div>
                <button
                  type="button"
                  onClick={onOpenAuth}
                  style={{ background: 'none', border: 'none', color: '#38BDF8', fontWeight: 700, fontSize: '0.75rem', cursor: 'pointer', padding: 0 }}
                >
                  Sign Up Free →
                </button>
              </div>

              <div style={{ height: '6px', background: 'rgba(255, 255, 255, 0.1)', borderRadius: '3px', overflow: 'hidden', marginBottom: '6px' }}>
                <div style={{
                  height: '100%',
                  width: `${Math.min(100, (guestUsesCount / 3) * 100)}%`,
                  background: guestUsesCount >= 3 ? '#EF4444' : '#F59E0B',
                  borderRadius: '3px'
                }} />
              </div>

              <div style={{ fontSize: '0.74rem', color: '#94A3B8' }}>
                {guestUsesCount >= 3
                  ? 'All 3 guest trials used. Create a free account to unlock 30 quizzes/month and 30 questions per test.'
                  : 'Create a free account to unlock 30 quizzes/month and up to 30 questions per test.'}
              </div>
            </div>
          )}

          <button
            onClick={
              !user && guestUsesCount >= 3
                ? onOpenAuth
                : isQuotaDepleted && onNavigateToPricing
                ? onNavigateToPricing
                : handleGenerate
            }
            disabled={loading || selectedFiles.length === 0}
            className="btn-primary"
            style={{
              width: '100%',
              justifyContent: 'center',
              padding: '15px',
              borderRadius: '14px',
              fontSize: '1rem',
              background: (!user && guestUsesCount >= 3) || isQuotaDepleted
                ? 'linear-gradient(135deg, #EF4444 0%, #DC2626 100%)'
                : undefined
            }}
          >
            {loading ? (
              <>
                <Loader2 size={18} className="spinner" /> Generating Questions...
              </>
            ) : !user && guestUsesCount >= 3 ? (
              <>
                <Lock size={20} /> 3 Guest Chances Used — Sign In / Sign Up
              </>
            ) : isQuotaDepleted ? (
              <>
                <Zap size={20} /> Monthly Limit Reached — Upgrade to Pro
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
          justifyContent: 'space-between',
          gap: '12px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <AlertCircle size={20} style={{ flexShrink: 0 }} />
            <span>{error}</span>
          </div>
          {(error.toLowerCase().includes('limit') || error.toLowerCase().includes('upgrade') || error.toLowerCase().includes('quota')) && onNavigateToPricing && (
            <button
              onClick={onNavigateToPricing}
              style={{
                background: 'linear-gradient(135deg, #6366F1 0%, #4F46E5 100%)',
                color: '#FFF',
                border: 'none',
                padding: '8px 16px',
                borderRadius: '10px',
                fontSize: '0.85rem',
                fontWeight: 700,
                cursor: 'pointer',
                whiteSpace: 'nowrap',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                boxShadow: '0 2px 10px rgba(99, 102, 241, 0.4)'
              }}
            >
              <Zap size={14} /> Upgrade Plan
            </button>
          )}
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
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '4px', flexWrap: 'wrap' }}>
                <span className="badge badge-emerald"><CheckCircle size={12} /> Generation Complete</span>
                <span className="badge badge-indigo">{questions.length} Questions</span>
                <span className="badge" style={{ background: 'rgba(56, 189, 248, 0.15)', color: '#38BDF8', border: '1px solid rgba(56, 189, 248, 0.3)' }}>
                  ⏱️ Saved ~{Math.round(questions.length * 3)}m of prep time
                </span>
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

      {/* Animated Visual Progress Bar Modal */}
      {progressModalOpen && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(9, 13, 22, 0.8)',
          backdropFilter: 'blur(10px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 9999,
          padding: '20px'
        }}>
          <div className="glass-panel" style={{
            padding: '32px 36px',
            maxWidth: '500px',
            width: '100%',
            textAlign: 'center',
            borderRadius: '24px',
            border: '1px solid rgba(99, 102, 241, 0.35)',
            boxShadow: '0 25px 50px rgba(0, 0, 0, 0.5)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '20px' }}>
              {progressStatus === 'completed' ? (
                <div style={{
                  padding: '16px',
                  borderRadius: '50%',
                  background: 'rgba(16, 185, 129, 0.18)',
                  border: '1px solid rgba(16, 185, 129, 0.4)'
                }}>
                  <CheckCircle size={44} color="#10B981" />
                </div>
              ) : (
                <div style={{
                  padding: '16px',
                  borderRadius: '50%',
                  background: 'rgba(99, 102, 241, 0.18)',
                  border: '1px solid rgba(99, 102, 241, 0.4)'
                }} className="pulse-glow">
                  <Brain size={44} color="#818CF8" className="spinner" />
                </div>
              )}
            </div>

            <h3 style={{ fontSize: '1.35rem', fontWeight: 800, color: '#F8FAFC', marginBottom: '6px' }}>
              Generating Question Bank
            </h3>
            
            <p style={{ color: '#94A3B8', fontSize: '0.88rem', marginBottom: '24px', lineHeight: 1.4, minHeight: '40px' }}>
              {progressStage}
            </p>

            {/* Animated Progress Bar */}
            <div style={{ width: '100%', marginBottom: '12px' }}>
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '8px',
                fontSize: '0.82rem',
                fontWeight: 700,
                color: '#CBD5E1'
              }}>
                <span>Processing Pipeline</span>
                <span style={{ color: '#818CF8', fontFamily: 'var(--font-mono)' }}>{progressPct}%</span>
              </div>

              <div style={{
                width: '100%',
                height: '12px',
                backgroundColor: 'rgba(30, 41, 59, 0.8)',
                borderRadius: '10px',
                overflow: 'hidden',
                padding: '2px',
                border: '1px solid rgba(255, 255, 255, 0.1)'
              }}>
                <div style={{
                  height: '100%',
                  width: `${Math.min(100, Math.max(0, progressPct))}%`,
                  borderRadius: '8px',
                  background: 'linear-gradient(90deg, #6366F1 0%, #8B5CF6 50%, #10B981 100%)',
                  transition: 'width 0.4s ease-in-out',
                  boxShadow: '0 0 16px rgba(99, 102, 241, 0.6)'
                }} />
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'center', gap: '8px', marginTop: '16px' }}>
              <span className="badge badge-indigo" style={{ fontSize: '0.75rem' }}>
                <Sparkles size={11} /> {selectedFiles.length} Doc{selectedFiles.length > 1 ? 's' : ''}
              </span>
              <span className="badge badge-purple" style={{ fontSize: '0.75rem' }}>
                Target: {bloomsParam.toUpperCase()}
              </span>
              <span className="badge badge-emerald" style={{ fontSize: '0.75rem' }}>
                {numQuestions} Qs
              </span>
            </div>
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
        user={user}
        onOpenAuth={onOpenAuth}
      />
    </div>
  );
};
