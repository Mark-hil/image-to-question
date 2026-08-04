import React, { useState } from 'react';
import type { QuestionData } from '../services/api';
import { Edit3, Check, Trash2, HelpCircle, Eye, EyeOff, CheckCircle2 } from 'lucide-react';

interface QuestionCardProps {
  index: number;
  question: QuestionData;
  onUpdate: (updated: QuestionData) => void;
  onDelete: () => void;
}

export const QuestionCard: React.FC<QuestionCardProps> = ({
  index,
  question,
  onUpdate,
  onDelete,
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [showAnswer, setShowAnswer] = useState(true);

  // Edit states
  const [qText, setQText] = useState(question.question_text || (question as any).question || '');
  const [aText, setAText] = useState(question.answer_text || (question as any).answer || '');
  const [rationaleText, setRationaleText] = useState(question.rationale || '');
  const [choicesList, setChoicesList] = useState<string[]>(question.choices || []);

  const handleSave = () => {
    onUpdate({
      ...question,
      question_text: qText,
      answer_text: aText,
      rationale: rationaleText,
      choices: choicesList,
    });
    setIsEditing(false);
  };

  const handleChoiceChange = (cIndex: number, val: string) => {
    const updated = [...choicesList];
    updated[cIndex] = val;
    setChoicesList(updated);
  };

  const currentQText = question.question_text || (question as any).question || '';
  const currentAText = question.answer_text || (question as any).answer || '';

  return (
    <div className="glass-panel-interactive" style={{ padding: '24px', position: 'relative', borderRadius: '18px' }}>
      {/* Header Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px', flexWrap: 'wrap', gap: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span style={{
            background: 'linear-gradient(135deg, #6366F1 0%, #4F46E5 100%)',
            color: '#FFF',
            fontWeight: 800,
            fontSize: '0.9rem',
            width: '32px',
            height: '32px',
            borderRadius: '10px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 4px 12px rgba(99, 102, 241, 0.3)'
          }}>
            {index}
          </span>
          <span className="badge badge-indigo">{(question.qtype || (question as any).type || 'MCQ').toUpperCase()}</span>

          <span className="badge badge-emerald">{(question.difficulty || 'Medium').toUpperCase()}</span>

          {question.class_id && (
            <span
              className="badge"
              style={{
                background: 'rgba(236, 72, 153, 0.15)',
                color: '#F472B6',
                border: '1px solid rgba(236, 72, 153, 0.3)',
                fontWeight: 700
              }}
              title={`Target Class/Grade: ${question.class_id}`}
            >
              🏫 {question.class_id}
            </span>
          )}

          {/* Bloom's Taxonomy Badge */}
          {(() => {
            const level = question.blooms_level || 'Understand';
            const bloomsMap: Record<string, { icon: string; color: string; bg: string; border: string }> = {
              Remember: { icon: '🧠', color: '#C084FC', bg: 'rgba(168, 85, 247, 0.16)', border: 'rgba(168, 85, 247, 0.35)' },
              Understand: { icon: '💡', color: '#38BDF8', bg: 'rgba(56, 189, 248, 0.16)', border: 'rgba(56, 189, 248, 0.35)' },
              Apply: { icon: '⚡', color: '#34D399', bg: 'rgba(52, 211, 153, 0.16)', border: 'rgba(52, 211, 153, 0.35)' },
              Analyze: { icon: '🔍', color: '#FBBF24', bg: 'rgba(251, 191, 36, 0.16)', border: 'rgba(251, 191, 36, 0.35)' },
              Evaluate: { icon: '⚖️', color: '#FB923C', bg: 'rgba(251, 146, 60, 0.16)', border: 'rgba(251, 146, 60, 0.35)' },
              Create: { icon: '🚀', color: '#F43F5E', bg: 'rgba(244, 63, 94, 0.16)', border: 'rgba(244, 63, 94, 0.35)' },
            };
            const config = bloomsMap[level] || bloomsMap['Understand'];
            return (
              <span
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '5px',
                  padding: '4px 10px',
                  borderRadius: '12px',
                  fontSize: '0.76rem',
                  fontWeight: 700,
                  color: config.color,
                  background: config.bg,
                  border: `1px solid ${config.border}`,
                  letterSpacing: '0.3px',
                }}
                title={`Bloom's Taxonomy Cognitive Classification: ${level}`}
              >
                <span>{config.icon}</span> {level.toUpperCase()}
              </span>
            );
          })()}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button
            onClick={() => setShowAnswer(!showAnswer)}
            className="btn-secondary"
            style={{ padding: '7px 14px', fontSize: '0.82rem', borderRadius: '10px' }}
          >
            {showAnswer ? <EyeOff size={14} /> : <Eye size={14} />} {showAnswer ? 'Hide Answer' : 'Show Answer'}
          </button>
          
          <button
            onClick={() => isEditing ? handleSave() : setIsEditing(true)}
            className={isEditing ? 'btn-primary' : 'btn-secondary'}
            style={{ padding: '7px 14px', fontSize: '0.82rem', borderRadius: '10px' }}
          >
            {isEditing ? <Check size={14} /> : <Edit3 size={14} />} {isEditing ? 'Done' : 'Edit'}
          </button>

          <button
            onClick={onDelete}
            className="btn-danger"
            style={{ padding: '7px 10px', borderRadius: '10px' }}
            title="Delete Question"
          >
            <Trash2 size={14} />
          </button>
        </div>
      </div>

      {/* Main Content */}
      {isEditing ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div className="form-group">
            <label className="form-label">Question Stem</label>
            <textarea
              className="input-field"
              rows={3}
              value={qText}
              onChange={(e) => setQText(e.target.value)}
            />
          </div>

          {choicesList.length > 0 && (
            <div className="form-group">
              <label className="form-label">Multiple Choice Options</label>
              {choicesList.map((choice, cIdx) => (
                <div key={cIdx} style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                  <span style={{ fontWeight: 700, color: '#818CF8', width: '20px' }}>
                    {String.fromCharCode(65 + cIdx)}.
                  </span>
                  <input
                    className="input-field"
                    style={{ flex: 1 }}
                    value={choice}
                    onChange={(e) => handleChoiceChange(cIdx, e.target.value)}
                  />
                </div>
              ))}
            </div>
          )}

          <div className="form-group">
            <label className="form-label">Correct Answer</label>
            <input
              className="input-field"
              value={aText}
              onChange={(e) => setAText(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label className="form-label">Explanation / Pedagogical Rationale</label>
            <textarea
              className="input-field"
              rows={2}
              value={rationaleText}
              onChange={(e) => setRationaleText(e.target.value)}
            />
          </div>
        </div>
      ) : (
        <div>
          <h4 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '16px', lineHeight: 1.45, color: '#F8FAFC' }}>
            {currentQText}
          </h4>

          {/* Choices list */}
          {question.choices && question.choices.length > 0 && (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '12px', marginBottom: '18px' }}>
              {question.choices.map((choice, cIdx) => {
                const isCorrect = choice === currentAText || choice.trim().toLowerCase() === currentAText.trim().toLowerCase();
                return (
                  <div
                    key={cIdx}
                    style={{
                      padding: '12px 16px',
                      borderRadius: '12px',
                      background: showAnswer && isCorrect ? 'rgba(16, 185, 129, 0.14)' : 'rgba(255, 255, 255, 0.03)',
                      border: `1px solid ${showAnswer && isCorrect ? '#10B981' : 'rgba(255, 255, 255, 0.08)'}`,
                      fontSize: '0.92rem',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '10px',
                      transition: 'all 0.2s ease',
                      boxShadow: showAnswer && isCorrect ? '0 0 15px rgba(16, 185, 129, 0.15)' : 'none'
                    }}
                  >
                    <span style={{
                      fontWeight: 800,
                      color: showAnswer && isCorrect ? '#10B981' : '#818CF8',
                      background: showAnswer && isCorrect ? 'rgba(16, 185, 129, 0.2)' : 'rgba(99, 102, 241, 0.12)',
                      padding: '4px 10px',
                      borderRadius: '8px',
                      fontSize: '0.85rem'
                    }}>
                      {String.fromCharCode(65 + cIdx)}
                    </span>
                    <span style={{ color: showAnswer && isCorrect ? '#FFF' : '#CBD5E1', flex: 1 }}>{choice}</span>
                    {showAnswer && isCorrect && <CheckCircle2 size={16} color="#10B981" />}
                  </div>
                );
              })}
            </div>
          )}

          {/* Answer section */}
          {showAnswer && (
            <div style={{
              background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(16, 185, 129, 0.04) 100%)',
              borderLeft: '4px solid #10B981',
              padding: '14px 18px',
              borderRadius: '0 12px 12px 0',
              marginTop: '14px',
              border: '1px solid rgba(16, 185, 129, 0.2)'
            }}>
              <div style={{ fontWeight: 700, color: '#34D399', fontSize: '0.92rem', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <CheckCircle2 size={16} color="#10B981" /> Correct Answer: <span style={{ color: '#FFF' }}>{currentAText}</span>
              </div>
              {question.rationale && (
                <div style={{ fontSize: '0.88rem', color: '#94A3B8', display: 'flex', gap: '8px', marginTop: '6px' }}>
                  <HelpCircle size={16} color="#818CF8" style={{ flexShrink: 0, marginTop: '2px' }} />
                  <span><strong style={{ color: '#CBD5E1' }}>Rationale:</strong> {question.rationale}</span>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
