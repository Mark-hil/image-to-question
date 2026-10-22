import React, { useState, useEffect, useMemo } from 'react';
import { api } from '../services/api';
import type { EducationLevel, StageMetadata } from '../types/education';
import { GraduationCap, Sparkles, Search, ChevronDown, Check, AlertCircle } from 'lucide-react';

interface EducationLevelSelectorProps {
  selectedLevelCode: string;
  classLabel: string;
  onLevelChange: (levelCode: string, level: EducationLevel | null) => void;
  onClassLabelChange: (label: string) => void;
  hasError?: boolean;
}

const STAGE_ICONS: Record<string, React.ReactNode> = {
  early_years: <span style={{ fontSize: '1.1rem' }}>🧸</span>,
  primary: <span style={{ fontSize: '1.1rem' }}>🎒</span>,
  junior_secondary: <span style={{ fontSize: '1.1rem' }}>📘</span>,
  senior_secondary: <span style={{ fontSize: '1.1rem' }}>📐</span>,
  diploma: <span style={{ fontSize: '1.1rem' }}>📜</span>,
  undergraduate: <span style={{ fontSize: '1.1rem' }}>🏛️</span>,
  postgraduate: <span style={{ fontSize: '1.1rem' }}>🔬</span>,
  doctoral: <span style={{ fontSize: '1.1rem' }}>🎓</span>,
  professional: <span style={{ fontSize: '1.1rem' }}>💼</span>,
};

const STAGE_THEME: Record<string, { color: string; bg: string; border: string }> = {
  early_years: { color: '#F472B6', bg: 'rgba(244, 114, 182, 0.12)', border: 'rgba(244, 114, 182, 0.3)' },
  primary: { color: '#10B981', bg: 'rgba(16, 185, 129, 0.12)', border: 'rgba(16, 185, 129, 0.3)' },
  junior_secondary: { color: '#06B6D4', bg: 'rgba(6, 182, 212, 0.12)', border: 'rgba(6, 182, 212, 0.3)' },
  senior_secondary: { color: '#3B82F6', bg: 'rgba(59, 130, 246, 0.12)', border: 'rgba(59, 130, 246, 0.3)' },
  diploma: { color: '#14B8A6', bg: 'rgba(20, 184, 166, 0.12)', border: 'rgba(20, 184, 166, 0.3)' },
  undergraduate: { color: '#6366F1', bg: 'rgba(99, 102, 241, 0.12)', border: 'rgba(99, 102, 241, 0.3)' },
  postgraduate: { color: '#8B5CF6', bg: 'rgba(139, 92, 246, 0.12)', border: 'rgba(139, 92, 246, 0.3)' },
  doctoral: { color: '#EC4899', bg: 'rgba(236, 72, 153, 0.12)', border: 'rgba(236, 72, 153, 0.3)' },
  professional: { color: '#F59E0B', bg: 'rgba(245, 158, 11, 0.12)', border: 'rgba(245, 158, 11, 0.3)' },
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

  // Automatically open picker if hasError is triggered when user attempts to submit without a level
  useEffect(() => {
    if (hasError && !selectedLevelCode) {
      setIsOpen(true);
    }
  }, [hasError, selectedLevelCode]);

  // Fetch catalog on mount (do NOT auto-select so user is prompted to pick explicitly)
  useEffect(() => {
    let isMounted = true;
    api.getEducationLevels()
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
    return levels.filter((lvl) => {
      const matchesStage = activeStage === 'all' || lvl.stage === activeStage;
      const matchesSearch =
        searchQuery === '' ||
        lvl.label.toLowerCase().includes(searchQuery.toLowerCase()) ||
        lvl.code.toLowerCase().includes(searchQuery.toLowerCase()) ||
        lvl.description.toLowerCase().includes(searchQuery.toLowerCase());
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
    ? (STAGE_THEME[currentLevel.stage] || STAGE_THEME.senior_secondary)
    : hasError
    ? { color: '#EF4444', bg: 'rgba(239, 68, 68, 0.12)', border: 'rgba(239, 68, 68, 0.35)' }
    : { color: '#818CF8', bg: 'rgba(99, 102, 241, 0.12)', border: 'rgba(99, 102, 241, 0.3)' };

  return (
    <div className="education-level-selector" style={{ position: 'relative' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
        <label className="form-label" style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
          <GraduationCap size={16} color={theme.color} />
          <span>
            Target Education Level & Class <span style={{ color: '#EF4444', fontWeight: 'bold' }}>*</span>
          </span>
          <span
            className="badge"
            style={{
              background: theme.bg,
              color: theme.color,
              border: `1px solid ${theme.border}`,
              fontSize: '0.72rem',
              fontWeight: 700,
              padding: '2px 8px',
            }}
          >
            {currentLevel ? currentLevel.label : hasError ? '⚠️ Please Select Level' : 'Required — Click to Select'}
          </span>
        </label>
        <span style={{ fontSize: '0.75rem', color: hasError && !currentLevel ? '#F87171' : 'var(--text-muted)' }}>
          {currentLevel?.typical_age ? `Ages ${currentLevel.typical_age[0]}-${currentLevel.typical_age[1]}` : 'Required Field'}
        </span>
      </div>

      {/* Trigger Button / Header */}
      <div
        onClick={() => setIsOpen(!isOpen)}
        className="input-field"
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          cursor: 'pointer',
          padding: '10px 14px',
          border: hasError && !currentLevel
            ? '1.5px solid #EF4444'
            : `1px solid ${isOpen ? theme.color : 'rgba(255, 255, 255, 0.12)'}`,
          background: hasError && !currentLevel
            ? 'rgba(239, 68, 68, 0.06)'
            : 'rgba(255, 255, 255, 0.03)',
          boxShadow: hasError && !currentLevel
            ? '0 0 16px rgba(239, 68, 68, 0.25)'
            : 'none',
          borderRadius: '12px',
          transition: 'all 0.2s ease',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', overflow: 'hidden' }}>
          <span style={{ fontSize: '1.2rem' }}>
            {STAGE_ICONS[currentLevel?.stage || ''] || (hasError ? '⚠️' : '🎓')}
          </span>
          <div style={{ textAlign: 'left' }}>
            <div style={{ fontWeight: 600, fontSize: '0.92rem', color: hasError && !currentLevel ? '#FCA5A5' : currentLevel ? 'var(--text-main)' : '#CBD5E1' }}>
              {currentLevel?.label || 'Select Target Education Level (Required) *'}
            </div>
            <div style={{ fontSize: '0.75rem', color: hasError && !currentLevel ? '#F87171' : 'var(--text-muted)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
              {currentLevel?.description || (hasError ? 'Action required: Choose an education level to proceed' : 'Primary Class 1 up to PhD Research Tier')}
            </div>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span
            className="badge"
            style={{
              background: 'rgba(255, 255, 255, 0.08)',
              color: 'var(--text-muted)',
              fontSize: '0.7rem',
              padding: '2px 6px',
            }}
          >
            {currentLevel?.max_choices || 4} Choices
          </span>
          <ChevronDown
            size={16}
            style={{
              transform: isOpen ? 'rotate(180deg)' : 'none',
              transition: 'transform 0.2s ease',
              color: 'var(--text-muted)',
            }}
          />
        </div>
      </div>

      {/* Prominent Prompt Notice when error is active and no level selected */}
      {hasError && !currentLevel && (
        <div
          style={{
            marginTop: '8px',
            padding: '9px 12px',
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
            <strong>Education Level Required:</strong> Please select an education level from the menu below before generating questions.
          </span>
        </div>
      )}

      {/* Popover Level Picker */}
      {isOpen && (
        <div
          className="glass-panel"
          style={{
            position: 'absolute',
            top: 'calc(100% + 8px)',
            left: 0,
            right: 0,
            zIndex: 999,
            padding: '16px',
            borderRadius: '16px',
            boxShadow: '0 20px 40px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(255, 255, 255, 0.1)',
            maxHeight: '460px',
            display: 'flex',
            flexDirection: 'column',
            gap: '12px',
          }}
        >
          {/* Search Bar */}
          <div style={{ position: 'relative' }}>
            <Search size={14} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
            <input
              type="text"
              className="input-field"
              placeholder="Search level (e.g. Primary 1, JHS, Class 5, Uni Level 300, PhD)..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{ paddingLeft: '34px', fontSize: '0.85rem' }}
              autoFocus
            />
          </div>

          {/* Stage Tabs */}
          <div
            style={{
              display: 'flex',
              gap: '6px',
              overflowX: 'auto',
              paddingBottom: '4px',
              borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
            }}
          >
            <button
              type="button"
              onClick={() => setActiveStage('all')}
              style={{
                background: activeStage === 'all' ? 'rgba(99, 102, 241, 0.2)' : 'rgba(255, 255, 255, 0.04)',
                color: activeStage === 'all' ? '#818CF8' : 'var(--text-muted)',
                border: activeStage === 'all' ? '1px solid #6366F1' : '1px solid transparent',
                borderRadius: '8px',
                padding: '4px 10px',
                fontSize: '0.74rem',
                fontWeight: 600,
                cursor: 'pointer',
                whiteSpace: 'nowrap',
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
                    color: isActive ? sTheme.color : 'var(--text-muted)',
                    border: isActive ? `1px solid ${sTheme.border}` : '1px solid transparent',
                    borderRadius: '8px',
                    padding: '4px 10px',
                    fontSize: '0.74rem',
                    fontWeight: 600,
                    cursor: 'pointer',
                    whiteSpace: 'nowrap',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                  }}
                >
                  {STAGE_ICONS[stg.code]}
                  {stg.label.split(' / ')[0]}
                </button>
              );
            })}
          </div>

          {/* Level List */}
          <div
            style={{
              overflowY: 'auto',
              maxHeight: '260px',
              display: 'flex',
              flexDirection: 'column',
              gap: '6px',
              paddingRight: '4px',
            }}
          >
            {isLoading ? (
              <div style={{ textAlign: 'center', padding: '20px', color: 'var(--text-muted)' }}>
                Loading educational levels catalog...
              </div>
            ) : filteredLevels.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '20px', color: 'var(--text-muted)' }}>
                No levels match "{searchQuery}"
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
                      padding: '8px 12px',
                      borderRadius: '10px',
                      cursor: 'pointer',
                      background: isSelected ? sTheme.bg : 'rgba(255, 255, 255, 0.02)',
                      border: `1px solid ${isSelected ? sTheme.border : 'rgba(255, 255, 255, 0.05)'}`,
                      transition: 'all 0.15s ease',
                    }}
                    onMouseEnter={(e) => {
                      if (!isSelected) e.currentTarget.style.background = 'rgba(255, 255, 255, 0.06)';
                    }}
                    onMouseLeave={(e) => {
                      if (!isSelected) e.currentTarget.style.background = 'rgba(255, 255, 255, 0.02)';
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ fontSize: '1rem' }}>{STAGE_ICONS[lvl.stage]}</span>
                      <div>
                        <div style={{ fontWeight: isSelected ? 700 : 500, fontSize: '0.85rem', color: isSelected ? sTheme.color : 'var(--text-main)' }}>
                          {lvl.label}
                        </div>
                        <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                          {lvl.description}
                        </div>
                      </div>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      {lvl.typical_age && (
                        <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                          Age {lvl.typical_age[0]}-{lvl.typical_age[1]}
                        </span>
                      )}
                      {isSelected && <Check size={16} color={sTheme.color} />}
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      )}

      {/* Classroom Section / Specific Tag Input */}
      <div style={{ marginTop: '10px' }}>
        <label className="form-label" style={{ fontSize: '0.78rem', marginBottom: '4px', color: 'var(--text-muted)' }}>
          Classroom Section / Custom Cohort Label (Optional)
        </label>
        <input
          type="text"
          className="input-field"
          value={classLabel}
          onChange={(e) => onClassLabelChange(e.target.value)}
          placeholder={`e.g. ${currentLevel?.label || 'Primary Class 1'} - Section A, Fall Cohort`}
          style={{ fontSize: '0.85rem', padding: '8px 12px' }}
        />
      </div>

      {/* Pedagogical Hint Callout */}
      {currentLevel && (
        <div
          style={{
            marginTop: '8px',
            padding: '8px 12px',
            borderRadius: '10px',
            background: 'rgba(255, 255, 255, 0.02)',
            border: `1px solid rgba(255, 255, 255, 0.06)`,
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '0.74rem',
            color: 'var(--text-muted)',
          }}
        >
          <Sparkles size={13} color={theme.color} />
          <span>
            Calibrated for <strong style={{ color: theme.color }}>{currentLevel.label}</strong>: vocabulary, distractors, and Bloom's difficulty will be tailored specifically for this tier.
          </span>
        </div>
      )}
    </div>
  );
};
