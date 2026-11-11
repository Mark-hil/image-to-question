import React, { useState, useEffect, useMemo, useRef } from 'react';
import { api } from '../services/api';
import type { EducationLevel, StageMetadata } from '../types/education';
import {
  GraduationCap,
  Sparkles,
  Search,
  ChevronDown,
  Check,
  AlertCircle,
  X,
} from 'lucide-react';

interface EducationLevelSelectorProps {
  selectedLevelCode: string;
  classLabel: string;
  onLevelChange: (levelCode: string, level: EducationLevel | null) => void;
  onClassLabelChange: (label: string) => void;
  hasError?: boolean;
}

const STAGE_ICONS: Record<string, React.ReactNode> = {
  early_years: <span style={{ fontSize: '1.05rem', lineHeight: 1 }}>🧸</span>,
  primary: <span style={{ fontSize: '1.05rem', lineHeight: 1 }}>🎒</span>,
  junior_secondary: <span style={{ fontSize: '1.05rem', lineHeight: 1 }}>📘</span>,
  senior_secondary: <span style={{ fontSize: '1.05rem', lineHeight: 1 }}>📐</span>,
  diploma: <span style={{ fontSize: '1.05rem', lineHeight: 1 }}>📜</span>,
  undergraduate: <span style={{ fontSize: '1.05rem', lineHeight: 1 }}>🏛️</span>,
  postgraduate: <span style={{ fontSize: '1.05rem', lineHeight: 1 }}>🔬</span>,
  doctoral: <span style={{ fontSize: '1.05rem', lineHeight: 1 }}>🎓</span>,
  professional: <span style={{ fontSize: '1.05rem', lineHeight: 1 }}>💼</span>,
};

const STAGE_THEME: Record<string, { color: string; bg: string; border: string }> = {
  early_years: { color: '#F472B6', bg: 'rgba(244, 114, 182, 0.14)', border: 'rgba(244, 114, 182, 0.35)' },
  primary: { color: '#34D399', bg: 'rgba(16, 185, 129, 0.14)', border: 'rgba(16, 185, 129, 0.35)' },
  junior_secondary: { color: '#22D3EE', bg: 'rgba(6, 182, 212, 0.14)', border: 'rgba(6, 182, 212, 0.35)' },
  senior_secondary: { color: '#60A5FA', bg: 'rgba(59, 130, 246, 0.14)', border: 'rgba(59, 130, 246, 0.35)' },
  diploma: { color: '#2DD4BF', bg: 'rgba(20, 184, 166, 0.14)', border: 'rgba(20, 184, 166, 0.35)' },
  undergraduate: { color: '#818CF8', bg: 'rgba(99, 102, 241, 0.14)', border: 'rgba(99, 102, 241, 0.35)' },
  postgraduate: { color: '#A78BFA', bg: 'rgba(139, 92, 246, 0.14)', border: 'rgba(139, 92, 246, 0.35)' },
  doctoral: { color: '#F472B6', bg: 'rgba(236, 72, 153, 0.14)', border: 'rgba(236, 72, 153, 0.35)' },
  professional: { color: '#FBBF24', bg: 'rgba(245, 158, 11, 0.14)', border: 'rgba(245, 158, 11, 0.35)' },
};

export const EducationLevelSelector: React.FC<EducationLevelSelectorProps> = ({
  selectedLevelCode,
  classLabel,
  onLevelChange,
  onClassLabelChange,
  hasError = false,
}) => {
  const [levels, setLevels] = useState<EducationLevel[]>([]);
  const [stages, setStages] = useState<StageMetadata[]>([]);
  const [activeStage, setActiveStage] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [isOpen, setIsOpen] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const dropdownContainerRef = useRef<HTMLDivElement>(null);

  // Automatically open picker if hasError is triggered when user attempts to submit without a level
  useEffect(() => {
    if (hasError && !selectedLevelCode) {
      setIsOpen(true);
    }
  }, [hasError, selectedLevelCode]);

  // Close popover on outside click or Escape key
  useEffect(() => {
    if (!isOpen) return;
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownContainerRef.current && !dropdownContainerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen]);

  // Fetch catalog on mount
  useEffect(() => {
    let isMounted = true;
    api
      .getEducationLevels()
      .then((data) => {
        if (!isMounted) return;
        setLevels(data.levels || []);
        setStages(data.stages || []);
        setIsLoading(false);
      })
      .catch((err) => {
        console.error('Failed to load education catalog:', err);
        setIsLoading(false);
      });
    return () => {
      isMounted = false;
    };
  }, []);

  const currentLevel = useMemo(() => {
    return levels.find((l) => l.code === selectedLevelCode) || null;
  }, [levels, selectedLevelCode]);

  // Synchronize active stage when selected level changes
  useEffect(() => {
    if (currentLevel && activeStage === 'all') {
      setActiveStage(currentLevel.stage);
    }
  }, [currentLevel]);

  // Filtered levels based on search and stage filter
  const filteredLevels = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    return levels.filter((lvl) => {
      const matchesStage = activeStage === 'all' || lvl.stage === activeStage;
      const matchesSearch =
        q === '' ||
        lvl.label.toLowerCase().includes(q) ||
        lvl.code.toLowerCase().includes(q) ||
        lvl.description.toLowerCase().includes(q);
      return matchesStage && matchesSearch;
    });
  }, [levels, activeStage, searchQuery]);

  const handleSelectLevel = (lvl: EducationLevel) => {
    onLevelChange(lvl.code, lvl);
    if (!classLabel || classLabel === currentLevel?.label) {
      onClassLabelChange(lvl.label);
    }
    setIsOpen(false);
  };

  const theme = currentLevel
    ? STAGE_THEME[currentLevel.stage] || STAGE_THEME.senior_secondary
    : hasError
    ? { color: '#EF4444', bg: 'rgba(239, 68, 68, 0.14)', border: 'rgba(239, 68, 68, 0.35)' }
    : { color: '#818CF8', bg: 'rgba(99, 102, 241, 0.14)', border: 'rgba(99, 102, 241, 0.32)' };

  return (
    <div className="education-level-selector" style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
      {/* Header Label Row */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '8px' }}>
        <label className="form-label" style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
          <GraduationCap size={16} color={theme.color} />
          <span style={{ color: '#E2E8F0', fontWeight: 600 }}>
            Target Education Level & Class <span style={{ color: '#EF4444', fontWeight: 700 }}>*</span>
          </span>
          <span
            className="badge"
            style={{
              background: theme.bg,
              color: theme.color,
              border: `1px solid ${theme.border}`,
              fontSize: '0.68rem',
              fontWeight: 700,
              padding: '2px 9px',
              letterSpacing: '0.04em',
            }}
          >
            {currentLevel ? currentLevel.label : hasError ? 'Please Select Level' : 'Required'}
          </span>
        </label>
        <span style={{ fontSize: '0.75rem', color: hasError && !currentLevel ? '#F87171' : '#94A3B8', fontWeight: 500 }}>
          {currentLevel?.typical_age ? `Ages ${currentLevel.typical_age[0]}–${currentLevel.typical_age[1]}` : 'Primary 1 → PhD'}
        </span>
      </div>

      {/* Trigger + Popover Anchor Wrapper */}
      <div ref={dropdownContainerRef} style={{ position: 'relative', zIndex: isOpen ? 50 : 'auto' }}>
        {/* Trigger Button */}
        <button
          type="button"
          onClick={() => setIsOpen((prev) => !prev)}
          aria-expanded={isOpen}
          style={{
            width: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '12px',
            cursor: 'pointer',
            padding: '12px 16px',
            border:
              hasError && !currentLevel
                ? '1.5px solid #EF4444'
                : isOpen
                ? `1.5px solid ${theme.color}`
                : '1px solid rgba(148, 163, 184, 0.2)',
            background:
              hasError && !currentLevel
                ? 'rgba(239, 68, 68, 0.08)'
                : isOpen
                ? '#131C31'
                : 'rgba(15, 23, 42, 0.85)',
            boxShadow:
              hasError && !currentLevel
                ? '0 0 0 3px rgba(239, 68, 68, 0.15)'
                : isOpen
                ? `0 0 0 3px ${theme.bg}`
                : 'none',
            borderRadius: '12px',
            transition: 'all 0.2s ease',
            color: 'inherit',
            fontFamily: 'inherit',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', minWidth: 0, flex: 1 }}>
            <div
              style={{
                width: '36px',
                height: '36px',
                borderRadius: '10px',
                background: theme.bg,
                border: `1px solid ${theme.border}`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
              }}
            >
              {STAGE_ICONS[currentLevel?.stage || ''] || <GraduationCap size={18} color={theme.color} />}
            </div>
            <div style={{ textAlign: 'left', minWidth: 0, flex: 1 }}>
              <div
                style={{
                  fontWeight: 600,
                  fontSize: '0.93rem',
                  color: hasError && !currentLevel ? '#FCA5A5' : currentLevel ? '#F8FAFC' : '#E2E8F0',
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                }}
              >
                {currentLevel?.label || 'Select Target Education Level...'}
              </div>
              <div
                style={{
                  fontSize: '0.76rem',
                  color: hasError && !currentLevel ? '#F87171' : '#94A3B8',
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  marginTop: '2px',
                }}
              >
                {currentLevel?.description ||
                  (hasError
                    ? 'Action required: Choose an education level to proceed'
                    : 'Choose grade, university tier, or professional certification')}
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexShrink: 0 }}>
            {currentLevel && (
              <span
                style={{
                  background: 'rgba(255, 255, 255, 0.06)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  color: '#CBD5E1',
                  fontSize: '0.72rem',
                  fontWeight: 600,
                  padding: '3px 8px',
                  borderRadius: '6px',
                }}
              >
                {currentLevel.max_choices || 4} MCQ Choices
              </span>
            )}
            <ChevronDown
              size={18}
              style={{
                transform: isOpen ? 'rotate(180deg)' : 'none',
                transition: 'transform 0.2s ease',
                color: isOpen ? theme.color : '#94A3B8',
              }}
            />
          </div>
        </button>

        {/* Opaque Elevated Popover Menu */}
        {isOpen && (
          <div
            style={{
              position: 'absolute',
              top: 'calc(100% + 8px)',
              left: 0,
              right: 0,
              zIndex: 1000,
              background: '#0F172A',
              border: '1px solid rgba(129, 140, 248, 0.28)',
              borderRadius: '16px',
              padding: '16px',
              boxShadow: '0 24px 60px rgba(0, 0, 0, 0.85), 0 0 0 1px rgba(255, 255, 255, 0.06)',
              display: 'flex',
              flexDirection: 'column',
              gap: '12px',
            }}
          >
            {/* Full-Width Search Bar */}
            <div style={{ position: 'relative', width: '100%' }}>
              <Search
                size={15}
                style={{
                  position: 'absolute',
                  left: '13px',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  color: '#64748B',
                  pointerEvents: 'none',
                }}
              />
              <input
                type="text"
                className="input-field"
                placeholder="Search grade or tier (e.g. Primary 1, JSS 2, Grade 11, Level 300, PhD)..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                style={{
                  width: '100%',
                  padding: '10px 36px 10px 38px',
                  fontSize: '0.86rem',
                  background: '#1E293B',
                  border: '1px solid rgba(148, 163, 184, 0.22)',
                  borderRadius: '10px',
                  color: '#F8FAFC',
                }}
                autoFocus
              />
              {searchQuery && (
                <button
                  type="button"
                  onClick={() => setSearchQuery('')}
                  aria-label="Clear search"
                  style={{
                    position: 'absolute',
                    right: '10px',
                    top: '50%',
                    transform: 'translateY(-50%)',
                    background: 'rgba(148, 163, 184, 0.16)',
                    border: 'none',
                    borderRadius: '6px',
                    width: '22px',
                    height: '22px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: '#CBD5E1',
                    cursor: 'pointer',
                  }}
                >
                  <X size={13} />
                </button>
              )}
            </div>

            {/* Clean Wrapping Stage Filter Pills (No Horizontal Scrollbar) */}
            <div
              style={{
                display: 'flex',
                flexWrap: 'wrap',
                gap: '6px',
                paddingBottom: '10px',
                borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
              }}
            >
              <button
                type="button"
                onClick={() => setActiveStage('all')}
                style={{
                  background: activeStage === 'all' ? 'rgba(99, 102, 241, 0.22)' : 'rgba(255, 255, 255, 0.04)',
                  color: activeStage === 'all' ? '#A5B4FC' : '#94A3B8',
                  border: activeStage === 'all' ? '1px solid #6366F1' : '1px solid rgba(255, 255, 255, 0.06)',
                  borderRadius: '8px',
                  padding: '5px 10px',
                  fontSize: '0.74rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  whiteSpace: 'nowrap',
                  transition: 'all 0.15s ease',
                }}
              >
                All Stages
              </button>
              {stages.map((stg) => {
                const isActive = activeStage === stg.code;
                const sTheme = STAGE_THEME[stg.code] || STAGE_THEME.senior_secondary;
                return (
                  <button
                    key={stg.code}
                    type="button"
                    onClick={() => setActiveStage(stg.code)}
                    style={{
                      background: isActive ? sTheme.bg : 'rgba(255, 255, 255, 0.04)',
                      color: isActive ? sTheme.color : '#94A3B8',
                      border: isActive ? `1px solid ${sTheme.border}` : '1px solid rgba(255, 255, 255, 0.06)',
                      borderRadius: '8px',
                      padding: '5px 10px',
                      fontSize: '0.74rem',
                      fontWeight: 600,
                      cursor: 'pointer',
                      whiteSpace: 'nowrap',
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '5px',
                      transition: 'all 0.15s ease',
                    }}
                  >
                    {STAGE_ICONS[stg.code]}
                    <span>{stg.label.split(' / ')[0]}</span>
                  </button>
                );
              })}
            </div>

            {/* Level Options List */}
            <div
              style={{
                overflowY: 'auto',
                maxHeight: '280px',
                display: 'flex',
                flexDirection: 'column',
                gap: '6px',
                paddingRight: '4px',
              }}
            >
              {isLoading ? (
                <div style={{ textAlign: 'center', padding: '24px', color: '#94A3B8', fontSize: '0.85rem' }}>
                  Loading educational levels catalog...
                </div>
              ) : filteredLevels.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '24px', color: '#94A3B8', fontSize: '0.85rem' }}>
                  No levels match "{searchQuery}".{' '}
                  {activeStage !== 'all' && (
                    <button
                      type="button"
                      onClick={() => setActiveStage('all')}
                      style={{
                        background: 'none',
                        border: 'none',
                        color: '#818CF8',
                        textDecoration: 'underline',
                        cursor: 'pointer',
                        fontWeight: 600,
                        padding: 0,
                      }}
                    >
                      Search all stages
                    </button>
                  )}
                </div>
              ) : (
                filteredLevels.map((lvl) => {
                  const isSelected = lvl.code === selectedLevelCode;
                  const sTheme = STAGE_THEME[lvl.stage] || STAGE_THEME.senior_secondary;

                  return (
                    <div
                      key={lvl.code}
                      onClick={() => handleSelectLevel(lvl)}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        gap: '12px',
                        padding: '10px 12px',
                        borderRadius: '10px',
                        cursor: 'pointer',
                        background: isSelected ? sTheme.bg : '#162033',
                        border: `1px solid ${isSelected ? sTheme.border : 'rgba(255, 255, 255, 0.06)'}`,
                        transition: 'all 0.15s ease',
                      }}
                      onMouseEnter={(e) => {
                        if (!isSelected) {
                          e.currentTarget.style.background = '#1E293B';
                          e.currentTarget.style.borderColor = 'rgba(148, 163, 184, 0.25)';
                        }
                      }}
                      onMouseLeave={(e) => {
                        if (!isSelected) {
                          e.currentTarget.style.background = '#162033';
                          e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.06)';
                        }
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'flex-start', gap: '10px', minWidth: 0, flex: 1 }}>
                        <span style={{ marginTop: '2px', flexShrink: 0 }}>{STAGE_ICONS[lvl.stage]}</span>
                        <div style={{ minWidth: 0 }}>
                          <div
                            style={{
                              fontWeight: isSelected ? 700 : 600,
                              fontSize: '0.87rem',
                              color: isSelected ? sTheme.color : '#F1F5F9',
                            }}
                          >
                            {lvl.label}
                          </div>
                          <div
                            style={{
                              fontSize: '0.74rem',
                              color: '#94A3B8',
                              marginTop: '2px',
                              lineHeight: 1.35,
                            }}
                          >
                            {lvl.description}
                          </div>
                        </div>
                      </div>

                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexShrink: 0 }}>
                        {lvl.typical_age && (
                          <span
                            style={{
                              fontSize: '0.71rem',
                              color: '#94A3B8',
                              background: 'rgba(255, 255, 255, 0.05)',
                              padding: '2px 7px',
                              borderRadius: '6px',
                              whiteSpace: 'nowrap',
                            }}
                          >
                            Age {lvl.typical_age[0]}–{lvl.typical_age[1]}
                          </span>
                        )}
                        {isSelected && <Check size={16} color={sTheme.color} strokeWidth={2.5} />}
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        )}
      </div>

      {/* Error Prompt Notice */}
      {hasError && !currentLevel && (
        <div
          style={{
            padding: '10px 12px',
            borderRadius: '10px',
            background: 'rgba(239, 68, 68, 0.12)',
            border: '1px solid rgba(239, 68, 68, 0.35)',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '0.8rem',
            color: '#FCA5A5',
          }}
        >
          <AlertCircle size={15} color="#EF4444" style={{ flexShrink: 0 }} />
          <span>
            <strong>Education Level Required:</strong> Please select an education level from the menu above before generating questions.
          </span>
        </div>
      )}

      {/* Classroom Section / Specific Tag Input */}
      <div>
        <label className="form-label" style={{ fontSize: '0.78rem', marginBottom: '6px', color: '#94A3B8' }}>
          Classroom Section / Custom Cohort Label (Optional)
        </label>
        <input
          type="text"
          className="input-field"
          value={classLabel}
          onChange={(e) => onClassLabelChange(e.target.value)}
          placeholder={`e.g. ${currentLevel?.label || 'Primary Class 1'} - Section A, Fall Cohort`}
          style={{
            width: '100%',
            fontSize: '0.85rem',
            padding: '9px 14px',
            background: 'rgba(15, 23, 42, 0.85)',
            border: '1px solid rgba(148, 163, 184, 0.2)',
            borderRadius: '10px',
          }}
        />
      </div>

      {/* Pedagogical Hint Callout */}
      {currentLevel && (
        <div
          style={{
            padding: '9px 12px',
            borderRadius: '10px',
            background: 'rgba(255, 255, 255, 0.03)',
            border: '1px solid rgba(255, 255, 255, 0.08)',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '0.75rem',
            color: '#94A3B8',
          }}
        >
          <Sparkles size={14} color={theme.color} style={{ flexShrink: 0 }} />
          <span>
            Calibrated for <strong style={{ color: theme.color }}>{currentLevel.label}</strong>: vocabulary, distractors, and Bloom's difficulty will be tailored specifically for this tier.
          </span>
        </div>
      )}
    </div>
  );
};
