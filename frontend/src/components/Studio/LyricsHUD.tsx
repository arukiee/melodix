import React from 'react';
import type { LyricAlignment, LyricSyllable } from '../../api/practice';

interface LyricsHUDProps {
  lyricAlignment: LyricAlignment | null | undefined;
  currentSyllableIndex: number;       // which syllable is "active"
  style?: React.CSSProperties;
}

// How many syllables to show ahead/behind
const CONTEXT_BEHIND = 2;
const CONTEXT_AHEAD  = 4;

export const LyricsHUD: React.FC<LyricsHUDProps> = ({
  lyricAlignment,
  currentSyllableIndex,
  style,
}) => {
  if (!lyricAlignment || lyricAlignment.alignmentLevel === 'none' || !lyricAlignment.syllables || lyricAlignment.syllables.length === 0) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', justifyContent: 'center', color: 'var(--text-secondary, #9ca3af)', fontSize: '1rem', fontStyle: 'italic', ...style }}>
        <span>🎵 Instrumental section</span>
      </div>
    );
  }

  const { syllables, confidence, alignmentLevel } = lyricAlignment;
  const showWarning = confidence < 0.6;

  // Visible window of syllables
  const start = Math.max(0, currentSyllableIndex - CONTEXT_BEHIND);
  const end   = Math.min(syllables.length, currentSyllableIndex + CONTEXT_AHEAD + 1);
  const visible: (LyricSyllable & { globalIndex: number })[] = syllables
    .slice(start, end)
    .map((syl, i) => ({ ...syl, globalIndex: start + i }));

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: '6px',
        ...style,
      }}
    >
      {showWarning && (
        <span style={{ fontSize: '0.7rem', color: '#f59e0b', letterSpacing: '0.04em' }}>
          ⚠️ Lyrics may be approximate
        </span>
      )}

      {/* Syllable strip */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '2px', flexWrap: 'wrap', justifyContent: 'center' }}>
        {visible.map(({ text, globalIndex }) => {
          const isCurrent = globalIndex === currentSyllableIndex;
          const isPast    = globalIndex < currentSyllableIndex;
          const isEmpty   = !text || text.trim() === '';

          if (isEmpty && !isCurrent) return null;

          return (
            <span
              key={globalIndex}
              style={{
                fontSize: isCurrent ? '1.4rem' : '0.95rem',
                fontWeight: isCurrent ? 700 : 400,
                color: isCurrent
                  ? 'var(--accent-primary, #7c3aed)'
                  : isPast
                    ? 'var(--text-muted, #6b7280)'
                    : 'var(--text-secondary, #9ca3af)',
                background: isCurrent ? 'rgba(124,58,237,0.12)' : 'transparent',
                borderRadius: '6px',
                padding: isCurrent ? '2px 8px' : '2px 3px',
                transition: 'all 0.18s ease',
                transform: isCurrent ? 'scale(1.1)' : 'scale(1)',
                letterSpacing: alignmentLevel === 'line' ? '0.02em' : '0',
                display: 'inline-block',
                whiteSpace: 'nowrap',
              }}
            >
              {isEmpty ? '·' : text}
            </span>
          );
        })}
      </div>

      {/* Alignment level badge — shown only in dev / low confidence */}
      {showWarning && (
        <span style={{
          fontSize: '0.65rem',
          color: 'var(--text-muted, #6b7280)',
          fontStyle: 'italic',
        }}>
          {alignmentLevel} · {Math.round(confidence * 100)}% confidence
        </span>
      )}
    </div>
  );
};
