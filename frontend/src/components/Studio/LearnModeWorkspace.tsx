/**
 * LearnModeWorkspace — Level 1 & 2
 *
 * Level 1 (progressionMode = "wait"):
 *   One note shown at a time. Progression only advances when the student
 *   plays the correct pitch (via mic or virtual keyboard). No timing
 *   pressure. Enharmonic equivalents are accepted (D#5 == Eb5).
 *
 * Level 2 (progressionMode = "timed"):
 *   Notes scroll with the beat at the mission's BPM. Lyrics advance
 *   automatically. The highlighted key changes on schedule.
 */
import React, { useCallback, useEffect, useRef, useState } from 'react';
import type { PracticeMission, LyricAlignment } from '../../api/practice';
import { liveNoteDetector } from '../../services/liveNoteDetector';
import { PianoKeyboard } from './PianoKeyboard';
import { LyricsHUD } from './LyricsHUD';

// ---------------------------------------------------------------------------
// Pitch-class normalization (MIDI number comparison)
// ---------------------------------------------------------------------------
const PITCH_CLASS: Record<string, number> = {
  C: 0, 'C#': 1, Db: 1, D: 2, 'D#': 3, Eb: 3,
  E: 4, F: 5, 'F#': 6, Gb: 6, G: 7, 'G#': 8,
  Ab: 8, A: 9, 'A#': 10, Bb: 10, B: 11,
};

function noteToMidi(note: string): number | null {
  const m = note.trim().match(/^([A-G][#b]?)(\d+)$/);
  if (!m) return null;
  const pc = PITCH_CLASS[m[1]];
  if (pc === undefined) return null;
  return (parseInt(m[2], 10) + 1) * 12 + pc;
}

function notesMatch(expected: string, played: string): boolean {
  const a = noteToMidi(expected);
  const b = noteToMidi(played);
  if (a !== null && b !== null) return a === b;
  // Fallback: strip octave
  const bare = (n: string) => n.trim().replace(/\d+$/, '').toUpperCase();
  return bare(expected) === bare(played);
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

interface LearnModeWorkspaceProps {
  mission: PracticeMission;
  lyricAlignment: LyricAlignment | null | undefined;
  onComplete: (score?: number) => void;
}

export const LearnModeWorkspace: React.FC<LearnModeWorkspaceProps> = ({
  mission,
  lyricAlignment,
  onComplete,
}) => {
  const events      = mission.expectedEvents ?? [];
  const isWaitMode  = mission.progressionMode === 'wait';

  const [noteIndex,    setNoteIndex]    = useState(0);
  const [wrongCount,   setWrongCount]   = useState(0);
  const [feedback,     setFeedback]     = useState<'idle' | 'correct' | 'wrong'>('idle');
  const [pulseTrigger, setPulseTrigger] = useState(0);

  const timerRef   = useRef<ReturnType<typeof setInterval> | null>(null);
  const indexRef   = useRef(0); // keep a ref so the interval closure sees the latest value

  // Sync ref
  useEffect(() => { indexRef.current = noteIndex; }, [noteIndex]);

  const currentEvent  = events[noteIndex] ?? null;
  const isComplete    = events.length > 0 && noteIndex >= events.length;

  const calculateScore = useCallback(() => {
    if (events.length === 0) return 100;
    return wrongCount > 0 ? Math.max(50, Math.round((events.length / (events.length + wrongCount)) * 100)) : 100;
  }, [events.length, wrongCount]);

  // ---- Timed mode (Level 2) -----------------------------------------------
  useEffect(() => {
    if (isWaitMode || !mission.bpm || events.length === 0) return;

    const beatMs   = 60_000 / mission.bpm;
    const noteMs   = beatMs;              // one note per beat at slow tempo

    timerRef.current = setInterval(() => {
      setNoteIndex(prev => {
        const next = prev + 1;
        if (next >= events.length) {
          if (timerRef.current) clearInterval(timerRef.current);
          onComplete(100);
        }
        return next;
      });
    }, noteMs);

    return () => { if (timerRef.current) clearInterval(timerRef.current); };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mission.id]);

  // ---- Wait mode (Level 1) — live mic subscription -----------------------
  const advance = useCallback(() => {
    setFeedback('correct');
    setPulseTrigger(t => t + 1);
    setTimeout(() => setFeedback('idle'), 400);
    setNoteIndex(prev => prev + 1);
  }, []);

  useEffect(() => {
    if (!isWaitMode) return;
    const unsub = liveNoteDetector.subscribe((detected: string | null) => {
      if (!detected || !currentEvent) return;
      if (notesMatch(currentEvent.note, detected)) {
        advance();
      } else {
        setWrongCount(w => w + 1);
        setFeedback('wrong');
        setTimeout(() => setFeedback('idle'), 300);
      }
    });
    return unsub;
  }, [isWaitMode, currentEvent, advance]);

  // ---- Virtual keyboard handler (both modes) ------------------------------
  const handleKeyPress = (note: string) => {
    if (!currentEvent) return;
    if (isWaitMode) {
      if (notesMatch(currentEvent.note, note)) {
        advance();
      } else {
        setWrongCount(w => w + 1);
        setFeedback('wrong');
        setTimeout(() => setFeedback('idle'), 300);
      }
    }
  };

  // ---- Highlighted keys ---------------------------------------------------
  const highlightedKeys = currentEvent ? [currentEvent.note] : [];
  const upcomingNotes   = events.slice(noteIndex + 1, noteIndex + 5).map(e => e.note);

  // ---- Feedback ring colour -----------------------------------------------
  const ringColor = feedback === 'correct'
    ? '#22c55e'
    : feedback === 'wrong'
      ? '#ef4444'
      : 'var(--accent-primary, #7c3aed)';

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: '0',
        minHeight: '100vh',
        background: 'var(--bg-primary, #0f0f23)',
        fontFamily: 'Inter, system-ui, sans-serif',
      }}
    >
      {/* ── Top bar ────────────────────────────────────────────────────── */}
      <div style={{
        width: '100%',
        padding: '18px 28px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        background: 'var(--bg-card, #1a1a3e)',
        borderBottom: '1px solid var(--border-color, rgba(255,255,255,0.08))',
      }}>
        <div>
          <span style={{ fontSize: '0.7rem', color: '#22c55e', fontWeight: 700, letterSpacing: '0.12em', textTransform: 'uppercase' }}>
            🟢 {isWaitMode ? 'Level 1 — Learn' : 'Level 2 — Rhythm'}
          </span>
          <div style={{ fontSize: '1rem', fontWeight: 600, marginTop: '2px' }}>{mission.title}</div>
        </div>
        {/* Progress pill */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          background: 'rgba(255,255,255,0.05)',
          borderRadius: '100px',
          padding: '6px 14px',
          fontSize: '0.85rem',
        }}>
          <span style={{ color: 'var(--text-secondary, #9ca3af)' }}>Note</span>
          <span style={{ fontWeight: 700, color: 'var(--accent-primary, #7c3aed)' }}>
            {Math.min(noteIndex + 1, events.length)}/{events.length}
          </span>
        </div>
      </div>

      {/* ── Lyrics HUD ────────────────────────────────────────────────── */}
      {mission.levelNumber !== 1 && (
        <div style={{ width: '100%', padding: '24px 28px 12px', textAlign: 'center' }}>
          <LyricsHUD lyricAlignment={lyricAlignment} currentSyllableIndex={noteIndex} />
        </div>
      )}

      {/* ── Main focal area ───────────────────────────────────────────── */}
      <div style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '28px',
        padding: '24px 28px',
        width: '100%',
      }}>
        {isComplete ? (
          <div style={{ textAlign: 'center', animation: 'fadeIn 0.4s ease' }}>
            <div style={{ fontSize: '3rem' }}>🎉</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 700, marginTop: '12px' }}>Section complete!</div>
            <div style={{ fontSize: '1.1rem', color: '#22c55e', fontWeight: 600, marginTop: '6px' }}>
              Score: {calculateScore()}%
            </div>
            <button
              onClick={() => onComplete(calculateScore())}
              style={{
                marginTop: '20px',
                padding: '12px 32px',
                background: 'linear-gradient(135deg, #7c3aed, #4f46e5)',
                color: '#fff',
                border: 'none',
                borderRadius: '100px',
                fontSize: '1rem',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              Continue →
            </button>
          </div>
        ) : (
          <>
            {/* Visual Note Sequence Tracker (Prev -> Now -> Next) */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '20px', justifyContent: 'center', margin: '20px 0' }}>
              
              {/* Previous Note */}
              {noteIndex > 0 ? (
                <div style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  opacity: 0.5,
                  transform: 'scale(0.85)',
                  transition: 'all 0.3s ease',
                }}>
                  <span style={{ fontSize: '0.7rem', color: 'var(--text-muted, #6b7280)', textTransform: 'uppercase', marginBottom: '4px' }}>Prev</span>
                  <div style={{
                    width: '70px',
                    height: '70px',
                    borderRadius: '16px',
                    background: 'rgba(255,255,255,0.05)',
                    border: '1px solid var(--border-color, rgba(255,255,255,0.1))',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '1.3rem',
                    fontWeight: 700,
                    color: 'var(--text-secondary, #9ca3af)',
                  }}>
                    {events[noteIndex - 1]?.note}
                  </div>
                </div>
              ) : (
                <div style={{ width: '70px' }} />
              )}

              {/* Current Target Note (Hero Focus) */}
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', position: 'relative' }}>
                <span style={{ fontSize: '0.8rem', color: '#22c55e', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '6px' }}>
                  Target
                </span>
                <div
                  key={pulseTrigger}
                  style={{
                    width: '120px',
                    height: '120px',
                    borderRadius: '28px',
                    background: 'var(--bg-elevated, #242450)',
                    border: `3px solid ${ringColor}`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '2.8rem',
                    fontWeight: 900,
                    color: '#fff',
                    boxShadow: feedback === 'correct'
                      ? '0 0 35px rgba(34, 197, 94, 0.4)'
                      : feedback === 'wrong'
                        ? '0 0 35px rgba(239, 68, 68, 0.4)'
                        : '0 8px 32px rgba(0,0,0,0.4)',
                    transition: 'all 0.2s cubic-bezier(0.175, 0.885, 0.32, 1.275)',
                    transform: feedback !== 'idle' ? 'scale(1.08)' : 'scale(1)',
                  }}
                >
                  {currentEvent?.note ?? '—'}
                </div>
              </div>

              {/* Next Notes (Queue) */}
              <div style={{ display: 'flex', gap: '8px', opacity: 0.5, transform: 'scale(0.85)', transition: 'all 0.3s ease' }}>
                {upcomingNotes.map((note, i) => (
                  <div key={i} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                    <span style={{ fontSize: '0.7rem', color: 'var(--text-muted, #6b7280)', textTransform: 'uppercase', marginBottom: '4px' }}>
                      {i === 0 ? 'Next' : `+${i + 1}`}
                    </span>
                    <div style={{
                      width: '70px',
                      height: '70px',
                      borderRadius: '16px',
                      background: 'rgba(255,255,255,0.05)',
                      border: '1px solid var(--border-color, rgba(255,255,255,0.1))',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '1.3rem',
                      fontWeight: 700,
                      color: 'var(--text-secondary, #9ca3af)',
                    }}>
                      {note}
                    </div>
                  </div>
                ))}
              </div>

            </div>

            {/* Progress bar */}
            <div style={{ width: '100%', maxWidth: '420px' }}>
              <div style={{
                height: '6px',
                background: 'rgba(255,255,255,0.08)',
                borderRadius: '100px',
                overflow: 'hidden',
              }}>
                <div style={{
                  height: '100%',
                  width: `${(noteIndex / events.length) * 100}%`,
                  background: 'linear-gradient(90deg, #22c55e, #4ade80)',
                  borderRadius: '100px',
                  transition: 'width 0.3s ease',
                }} />
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '4px', fontSize: '0.7rem', color: 'var(--text-muted, #6b7280)' }}>
                <span>{noteIndex} done</span>
                <span>{events.length - noteIndex} remaining</span>
              </div>
            </div>

            {/* Wait mode prompt */}
            {isWaitMode && (
              <p style={{
                fontSize: '0.85rem',
                color: 'var(--text-secondary, #9ca3af)',
                textAlign: 'center',
                margin: 0,
              }}>
                Press the highlighted key on the piano to play
              </p>
            )}
          </>
        )}
      </div>

      {/* ── Piano ─────────────────────────────────────────────────────── */}
      <div style={{
        width: '100%',
        borderTop: '1px solid var(--border-color, rgba(255,255,255,0.08))',
        background: 'var(--bg-card, #1a1a3e)',
        padding: '16px 0 24px',
      }}>
        <PianoKeyboard
          highlightedNotes={highlightedKeys}
          onNotePlay={handleKeyPress}
        />
      </div>
    </div>
  );
};
