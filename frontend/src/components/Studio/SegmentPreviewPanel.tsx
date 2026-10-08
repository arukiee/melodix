import React from 'react';
import { Play, Square, Gauge, ArrowRight, Music, Volume2, CheckCircle2 } from 'lucide-react';
import styles from './SegmentPreviewPanel.module.css';

interface SegmentNote {
  note: string;
  hand?: 'right' | 'left';
  duration?: number;
}

interface SegmentPreviewPanelProps {
  segmentTitle: string;
  notes: Array<SegmentNote | string>;
  phase?: 1 | 2;
  isPlaying: boolean;
  playbackSpeed: number; // 1.0 or 0.6
  activeNoteIndex?: number;
  onPlay: () => void;
  onStop: () => void;
  onToggleSpeed: () => void;
  onReadyToPractice: () => void;
}

export const SegmentPreviewPanel: React.FC<SegmentPreviewPanelProps> = ({
  segmentTitle,
  notes,
  phase = 1,
  isPlaying,
  playbackSpeed,
  activeNoteIndex = -1,
  onPlay,
  onStop,
  onToggleSpeed,
  onReadyToPractice,
}) => {
  // Filter notes according to phase structure:
  // Phase 1: Right-hand melody only
  // Phase 2: Melody + Chords (both hands)
  const filteredNotes = notes.filter((n) => {
    if (typeof n === 'string') return true;
    if (phase === 1) {
      return !n.hand || n.hand === 'right';
    }
    return true; // Phase 2 shows both hands
  });

  const noteNames = filteredNotes.map((n) => (typeof n === 'string' ? n : n.note));

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div className={styles.badgeGroup}>
          <span className={styles.phaseBadge}>
            {phase === 1 ? 'Phase 1: Melody Preview' : 'Phase 2: Melody & Chords Preview'}
          </span>
          <span className={styles.speedBadge}>
            {playbackSpeed < 1 ? 'Slow (60%)' : 'Normal (100%)'}
          </span>
        </div>
        <h3 className={styles.title}>{segmentTitle}</h3>
        <p className={styles.subtitle}>
          {phase === 1
            ? 'Listen and observe the melody sequence before practicing.'
            : 'Listen to the full melody and chord harmony.'}
        </p>
      </div>

      {/* Note Sequence Visualization */}
      <div className={styles.sequenceWrapper}>
        <div className={styles.sequenceLabel}>
          <Music size={16} /> Note Sequence:
        </div>
        <div className={styles.notePills}>
          {noteNames.length === 0 ? (
            <span className={styles.emptyText}>No notes in segment</span>
          ) : (
            noteNames.map((name, idx) => {
              const isActive = idx === activeNoteIndex;
              return (
                <React.Fragment key={`${name}-${idx}`}>
                  <span className={`${styles.notePill} ${isActive ? styles.activePill : ''}`}>
                    {name}
                  </span>
                  {idx < noteNames.length - 1 && (
                    <ArrowRight size={14} className={styles.arrowIcon} />
                  )}
                </React.Fragment>
              );
            })
          )}
        </div>
      </div>

      {/* Control Actions */}
      <div className={styles.controlsBar}>
        <div className={styles.leftControls}>
          <button
            className={`${styles.btn} ${isPlaying ? styles.btnActive : styles.btnPrimary}`}
            onClick={isPlaying ? onStop : onPlay}
          >
            {isPlaying ? <Square size={18} /> : <Volume2 size={18} />}
            <span>{isPlaying ? 'Stop Preview' : 'Play It For Me'}</span>
          </button>

          <button
            className={`${styles.btn} ${styles.btnSecondary} ${playbackSpeed < 1 ? styles.speedActive : ''}`}
            onClick={onToggleSpeed}
            title="Toggle playback speed between Normal (100%) and Slow (60%)"
          >
            <Gauge size={16} />
            <span>{playbackSpeed < 1 ? 'Speed: 60% (Slow)' : 'Speed: 100%'}</span>
          </button>
        </div>

        <button className={`${styles.btn} ${styles.btnReady}`} onClick={onReadyToPractice}>
          <CheckCircle2 size={18} />
          <span>I'm Ready — Practice This</span>
        </button>
      </div>
    </div>
  );
};
