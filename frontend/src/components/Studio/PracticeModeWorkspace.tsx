/**
 * PracticeModeWorkspace — Levels 3, 4, 5, 6
 *
 * Implements:
 * 1. A central playback loop using `usePlaybackController` to sync audio + visuals.
 * 2. Listen & Watch tabs: Auto-advancing playhead with audio synthesizer & virtual keyboard highlighting.
 * 3. Play tab: Interactive practice where correct note keystroke advances current note.
 * 4. A clean, Synthesia-style horizontal scrolling note visualizer with a fixed Playhead bar.
 */
import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { Headphones, Eye, Play, Pause, RotateCcw } from 'lucide-react';
import type { PracticeMission, LyricAlignment, SongPhrase } from '../../api/practice';
import { PianoKeyboard } from './PianoKeyboard';
import { LyricsHUD } from './LyricsHUD';
import { usePlaybackController } from '../../services/usePlaybackController';
import { AdaptiveEngine, type AdaptiveEngineState } from '../../services/adaptiveEngine';

type PhraseTab = 'listen' | 'watch' | 'play';

interface PracticeModeWorkspaceProps {
  mission: PracticeMission;
  lyricAlignment: LyricAlignment | null | undefined;
  phrases: SongPhrase[] | null | undefined;
  onComplete: () => void;
}

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

export const PracticeModeWorkspace: React.FC<PracticeModeWorkspaceProps> = ({
  mission,
  lyricAlignment,
  phrases,
  onComplete,
}) => {
  const events = mission.expectedEvents ?? [];
  const isPhrase = mission.type === 'phrase_practice' || mission.type === 'phrase_learn';
  const phraseNum = (mission.phraseIndex ?? 0) + 1;
  const phraseOf = mission.phraseTotal ?? 1;

  const [phraseTab, setPhraseTab] = useState<PhraseTab>('listen');

  // Track player progress during "Play" tab
  const [playIndex, setPlayIndex] = useState(0);
  const [attempts, setAttempts] = useState(0);
  const [correctCount, setCorrectCount] = useState(0);
  const [accuracy, setAccuracy] = useState(100);

  // Timed Practice mode — when ON the playhead runs and timing is evaluated
  const [timedMode, setTimedMode] = useState(false);

  // Last note result for feedback UI
  const [lastResult, setLastResult] = useState<{
    result: 'correct' | 'incorrect' | 'early' | 'late';
    expectedPitch: string;
    timingDiffMs: number;
  } | null>(null);

  // Adaptive engine state (tempoMultiplier, assistanceLevel, lastAction, etc.)
  const [adaptiveState, setAdaptiveState] = useState<AdaptiveEngineState | null>(null);
  const [adaptiveToast, setAdaptiveToast] = useState<string | null>(null);

  // Ref to clear the feedback flash after 600 ms
  const feedbackTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const toastTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Initialize playback controller
  // In 'listen' and 'watch' modes we auto-synthesize notes
  const isAutoPlay = phraseTab === 'listen' || phraseTab === 'watch' || !isPhrase;
  const controller = usePlaybackController(events, mission.bpm || 60, isAutoPlay);

  // AdaptiveEngine instance — recreated only when the mission changes
  const adaptiveEngine = useMemo(
    () =>
      new AdaptiveEngine(
        [], // sections — populated from mission server data in future; [] is fine for per-note tracking
        [], // steps
        mission.bpm || 60,
        (state) => {
          setAdaptiveState(state);
          // ── Apply tempo changes to real playback ──
          if (state.tempoMultiplier !== undefined) {
            controller.setPlaybackRate(state.tempoMultiplier);
          }
          // Show adaptive toast when the engine fires an action
          if (state.actionMessage) {
            setAdaptiveToast(state.actionMessage);
            if (toastTimerRef.current) clearTimeout(toastTimerRef.current);
            toastTimerRef.current = setTimeout(() => setAdaptiveToast(null), 3500);
          }
        }
      ),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [mission.id]
  );

  // Reset play session states on tab switch or mission changes
  useEffect(() => {
    controller.stopPlayback();
    setPlayIndex(0);
    setAttempts(0);
    setCorrectCount(0);
    setAccuracy(100);
    setLastResult(null);
    setTimedMode(false);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [phraseTab, mission.id]);

  // When timedMode is ON in the play tab, start the playhead clock.
  // The clock ticks but autoPlayAudio=false so no auto-synthesis.
  useEffect(() => {
    if (timedMode && phraseTab === 'play') {
      controller.startPlayback();
    } else if (!timedMode) {
      controller.stopPlayback();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [timedMode, phraseTab]);

  // ──────────────────────────────────────────────────────────────────────────
  // handleKeyPress — pitch + optional timing evaluation
  // ──────────────────────────────────────────────────────────────────────────
  const TIMING_TOLERANCE_S = 0.15; // 150 ms window

  const handleKeyPress = (note: string) => {
    if (phraseTab !== 'play' && isPhrase) return;

    const targetNote = events[playIndex];
    if (!targetNote) return;

    const expectedPitch = targetNote.note;           // real field: "C4", "F#3", etc.
    const expectedTime  = targetNote.relative_time;  // real field: seconds from phrase start
    const pressTime     = timedMode ? controller.currentTime : 0; // 0 in wait-mode → diff is always 0

    const pitchOk = noteToMidi(note) === noteToMidi(expectedPitch);

    let result: 'correct' | 'incorrect' | 'early' | 'late';

    if (!pitchOk) {
      result = 'incorrect';
    } else if (!timedMode) {
      // Wait-mode: pitch-only, no clock running
      result = 'correct';
    } else {
      const diff = pressTime - expectedTime;
      if (Math.abs(diff) <= TIMING_TOLERANCE_S) result = 'correct';
      else if (diff < 0)                         result = 'early';
      else                                        result = 'late';
    }

    // ── Stale-state fix: compute everything from local vars ─────────────────
    const newAttempts     = attempts + 1;
    const isActuallyRight = result === 'correct';
    const newCorrectCount = correctCount + (isActuallyRight ? 1 : 0);
    const partialPoints   = result === 'early' || result === 'late' ? 0.5 : 0;
    const numerator       = newCorrectCount + (isActuallyRight ? 0 : partialPoints);
    const newAccuracy     = Math.round((numerator / newAttempts) * 100);

    setAttempts(newAttempts);
    if (isActuallyRight) setCorrectCount(newCorrectCount);
    setAccuracy(newAccuracy);

    // ── Feedback flash (cleared after 600 ms) ───────────────────────────────
    if (feedbackTimerRef.current) clearTimeout(feedbackTimerRef.current);
    setLastResult({
      result,
      expectedPitch,
      timingDiffMs: (pressTime - expectedTime) * 1000,
    });
    feedbackTimerRef.current = setTimeout(() => setLastResult(null), 600);

    // ── Feed adaptive engine ────────────────────────────────────────────────
    adaptiveEngine.recordNoteResult({
      expectedPitch: noteToMidi(expectedPitch),
      playedPitch: noteToMidi(note),
      timingDiffMs: (pressTime - expectedTime) * 1000,
      result,
    });

    // ── Advance only on correct ─────────────────────────────────────────────
    if (isActuallyRight) {
      const nextIdx = playIndex + 1;
      if (nextIdx >= events.length) {
        setPlayIndex(events.length);
        setTimeout(() => onComplete(), 800);
      } else {
        setPlayIndex(nextIdx);
      }
    }
  };

  // Helper mapping octave-agnostic roots to chord triads
  const getChordTriad = (noteName: string) => {
    const pitch = noteName.replace(/\d+$/, '');
    const map: Record<string, { label: string; keys: string[] }> = {
      'C':  { label: 'C Major', keys: ['C3', 'E3', 'G3'] },
      'C#': { label: 'C# Major', keys: ['C#3', 'F3', 'G#3'] },
      'Db': { label: 'Db Major', keys: ['Db3', 'F3', 'Ab3'] },
      'D':  { label: 'D Major', keys: ['D3', 'F#3', 'A3'] },
      'Eb': { label: 'Eb Major', keys: ['Eb3', 'G3', 'Bb3'] },
      'E':  { label: 'E Minor', keys: ['E3', 'G3', 'B3'] },
      'F':  { label: 'F Major', keys: ['F3', 'A3', 'C4'] },
      'F#': { label: 'F# Minor', keys: ['F#3', 'A3', 'C#4'] },
      'G':  { label: 'G Major', keys: ['G3', 'B3', 'D4'] },
      'Ab': { label: 'Ab Major', keys: ['Ab3', 'C4', 'Eb4'] },
      'A':  { label: 'A Minor', keys: ['A3', 'C4', 'E4'] },
      'Bb': { label: 'Bb Major', keys: ['Bb3', 'D4', 'F4'] },
      'B':  { label: 'B Minor', keys: ['B3', 'D4', 'F#4'] },
    };
    return map[pitch] || { label: `${pitch} Chord`, keys: [noteName] };
  };

  // Get active chord info for Level 3
  const activeEvent = phraseTab === 'play' ? events[playIndex] : events[controller.currentSyllableIndex];
  const chordInfo = activeEvent && mission.levelNumber === 3 ? getChordTriad(activeEvent.note) : null;

  // Determine current active notes for virtual piano highlighting
  let pianoHighlights: string[] = [];
  if (chordInfo) {
    // For Chord Practice (Level 3), highlight the full triad
    pianoHighlights = chordInfo.keys;
  } else if (phraseTab === 'play') {
    // In play tab, highlight the upcoming target note
    if (events[playIndex]) {
      pianoHighlights = [events[playIndex].note];
    }
  } else {
    // In watch/listen tabs, highlight the currently playing note from controller
    pianoHighlights = controller.activeNotes;
  }

  // Active syllable index
  const activeSyllableIdx = phraseTab === 'play' ? playIndex : controller.currentSyllableIndex;

  const levelBadge = {
    3: { emoji: '🔵', label: 'Step 3 — Learn the Chords', color: '#3b82f6' },
    4: { emoji: '🔵', label: 'Step 4 — Melody + Chords + Lyrics', color: '#3b82f6' },
  }[mission.levelNumber ?? 4] ?? { emoji: '🔵', label: 'Practice', color: '#3b82f6' };

  // Pixels per second for scrolling notes
  const pxPerSec = 110;
  const playheadX = 250; // offset of playhead line in pixels

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      minHeight: '100vh',
      background: 'var(--bg-primary, #0f0f23)',
      fontFamily: 'Inter, system-ui, sans-serif',
      color: '#fff',
    }}>
      {/* ── Top bar ──────────────────────────────────────────────────── */}
      <div style={{
        padding: '16px 28px',
        background: 'var(--bg-card, #1a1a3e)',
        borderBottom: '1px solid var(--border-color, rgba(255,255,255,0.08))',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
      }}>
        <div>
          <span style={{ fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.12em', textTransform: 'uppercase', color: levelBadge.color }}>
            {levelBadge.emoji} {levelBadge.label}
          </span>
          <div style={{ fontSize: '1rem', fontWeight: 600, marginTop: '2px' }}>
            {isPhrase ? `Phrase ${phraseNum} of ${phraseOf}` : mission.title}
          </div>
        </div>
        <div style={{
          display: 'flex',
          gap: '12px',
          alignItems: 'center',
        }}>
          {isPhrase && (
            <div style={{
              fontSize: '0.8rem',
              color: 'var(--text-secondary, #9ca3af)',
              background: 'rgba(255,255,255,0.03)',
              padding: '4px 10px',
              borderRadius: '6px',
            }}>
              Mode: <strong style={{ textTransform: 'uppercase' }}>{phraseTab}</strong>
            </div>
          )}
          <div style={{
            fontSize: '0.85rem',
            background: 'rgba(255,255,255,0.05)',
            borderRadius: '100px',
            padding: '5px 14px',
          }}>
            Accuracy <strong style={{ color: accuracy >= 80 ? '#22c55e' : '#f59e0b' }}>{accuracy}%</strong>
          </div>
        </div>
      </div>

      {/* ── Phrase sub-tabs (Level 3 only) ───────────────────────────── */}
      {isPhrase && (
        <div style={{
          display: 'flex',
          background: 'var(--bg-card, #1a1a3e)',
          borderBottom: '1px solid var(--border-color, rgba(255,255,255,0.08))',
        }}>
          {(['listen', 'watch', 'play'] as PhraseTab[]).map(tab => {
            const label = tab === 'listen' ? '🎧 Listen' : tab === 'watch' ? '👀 Watch' : '🎹 Play';
            const active = phraseTab === tab;
            return (
              <button
                key={tab}
                onClick={() => setPhraseTab(tab)}
                style={{
                  flex: 1,
                  padding: '12px',
                  background: active ? 'rgba(59,130,246,0.15)' : 'transparent',
                  border: 'none',
                  borderBottom: active ? '3px solid #3b82f6' : '3px solid transparent',
                  color: active ? '#3b82f6' : 'var(--text-secondary, #9ca3af)',
                  fontWeight: active ? 700 : 400,
                  fontSize: '0.85rem',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                }}
              >
                {label}
              </button>
            );
          })}
        </div>
      )}

      {/* ── Lyrics HUD ───────────────────────────────────────────────── */}
      <div style={{ padding: '20px 28px 8px', textAlign: 'center' }}>
        <LyricsHUD lyricAlignment={lyricAlignment} currentSyllableIndex={activeSyllableIdx} />
      </div>

      {/* ── Visual Playback / Scrolling Notes Track ─────────────────── */}
      <div style={{
        flex: 1,
        padding: '20px 28px',
        display: 'flex',
        flexDirection: 'column',
        gap: '24px',
        justifyContent: 'center',
      }}>
        {/* Playback Controls Row (Listen/Watch or Timed) */}
        {isAutoPlay && (
          <div style={{ display: 'flex', justifyContent: 'center', gap: '14px', alignItems: 'center' }}>
            <button
              onClick={controller.isPlaying ? controller.pausePlayback : controller.startPlayback}
              style={{
                background: '#3b82f6',
                border: 'none',
                color: '#fff',
                width: '40px',
                height: '40px',
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                cursor: 'pointer',
                boxShadow: '0 4px 12px rgba(59,130,246,0.3)',
              }}
            >
              {controller.isPlaying ? <Pause size={18} /> : <Play size={18} style={{ marginLeft: '2px' }} />}
            </button>
            <button
              onClick={controller.stopPlayback}
              style={{
                background: 'rgba(255,255,255,0.06)',
                border: '1px solid var(--border-color)',
                color: 'var(--text-secondary)',
                width: '36px',
                height: '36px',
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                cursor: 'pointer',
              }}
            >
              <RotateCcw size={16} />
            </button>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
              {controller.currentTime.toFixed(1)}s / {controller.duration.toFixed(1)}s
            </span>
          </div>
        )}

        {/* ── Timed Practice toggle (Play tab only) ─────────────────── */}
        {phraseTab === 'play' && (
          <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '12px' }}>
            <button
              onClick={() => setTimedMode(m => !m)}
              style={{
                padding: '7px 18px',
                borderRadius: '20px',
                border: `1px solid ${timedMode ? '#f59e0b' : 'rgba(255,255,255,0.15)'}`,
                background: timedMode ? 'rgba(245,158,11,0.15)' : 'rgba(255,255,255,0.05)',
                color: timedMode ? '#f59e0b' : 'var(--text-secondary)',
                fontSize: '0.8rem',
                fontWeight: 600,
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                letterSpacing: '0.03em',
              }}
            >
              ⏱ Timed Practice: {timedMode ? 'ON' : 'OFF'}
            </button>
            {timedMode && (
              <span style={{ fontSize: '0.75rem', color: '#f59e0b', fontFamily: 'monospace' }}>
                {controller.currentTime.toFixed(2)}s
              </span>
            )}
          </div>
        )}

        {/* Scrolling Note Visualizer Container */}
        <div style={{
          position: 'relative',
          height: '140px',
          background: 'rgba(0,0,0,0.2)',
          borderRadius: '16px',
          border: '1px solid rgba(255,255,255,0.05)',
          overflow: 'hidden',
          boxShadow: 'inset 0 4px 20px rgba(0,0,0,0.4)',
        }}>
          {/* Static Playhead Cursor Bar */}
          <div style={{
            position: 'absolute',
            left: `${playheadX}px`,
            top: 0,
            bottom: 0,
            width: '2px',
            background: 'linear-gradient(180deg, transparent, #3b82f6, transparent)',
            boxShadow: '0 0 10px #3b82f6',
            zIndex: 10,
          }}>
            <span style={{
              position: 'absolute',
              top: '4px',
              left: '-20px',
              fontSize: '0.6rem',
              color: '#3b82f6',
              fontWeight: 700,
              letterSpacing: '0.05em',
            }}>NOW</span>
          </div>

          {/* Scrolling Tracks */}
          <div style={{
            position: 'absolute',
            left: 0,
            right: 0,
            top: 0,
            bottom: 0,
            // Slide notes to the left based on active playback time or player note index
            transform: `translateX(0px)`,
            transition: 'transform 0.1s linear',
          }}>
            {events.map((e, idx) => {
              // Calculate horizontal position relative to the playhead
              const timeOffset = phraseTab === 'play' 
                ? (events[idx].relative_time - (events[playIndex]?.relative_time || 0))
                : (e.relative_time - controller.currentTime);
              
              const leftPos = playheadX + (timeOffset * pxPerSec);
              const width = Math.max(30, e.duration * pxPerSec);

              const isCurrent = phraseTab === 'play' 
                ? idx === playIndex
                : (controller.currentTime >= e.relative_time && controller.currentTime <= e.relative_time + e.duration);

              const isPast = phraseTab === 'play' ? idx < playIndex : controller.currentTime > e.relative_time + e.duration;

              // Color notes differently based on play/past state
              const noteColor = isCurrent
                ? 'linear-gradient(135deg, #3b82f6, #1d4ed8)'
                : isPast
                  ? 'rgba(255,255,255,0.03)'
                  : 'rgba(59,130,246,0.3)';

              const borderColor = isCurrent ? '#60a5fa' : 'rgba(255,255,255,0.05)';

              // Map pitches to vertical rows to prevent overlapping of simultaneous notes
              const midiNum = noteToMidi(e.note) || 60;
              const row = (midiNum % 12) * 8; // distributed height

              return (
                <div
                  key={idx}
                  style={{
                    position: 'absolute',
                    left: `${leftPos}px`,
                    top: `${15 + row}px`,
                    width: `${width}px`,
                    height: '24px',
                    background: noteColor,
                    border: `1px solid ${borderColor}`,
                    borderRadius: '6px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '0.65rem',
                    fontWeight: 700,
                    color: isCurrent ? '#fff' : 'var(--text-secondary)',
                    boxShadow: isCurrent ? '0 0 12px rgba(59,130,246,0.6)' : 'none',
                    transition: 'left 0.1s linear, background 0.2s',
                  }}
                >
                  {e.note}
                </div>
              );
            })}
          </div>
        </div>

        {/* Accuracy and progress metadata */}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          fontSize: '0.8rem',
          color: 'var(--text-secondary, #9ca3af)',
          padding: '0 8px',
        }}>
          <span>Tempo <strong>{mission.bpm} BPM</strong></span>
          <span>Progress <strong>{phraseTab === 'play' ? playIndex : controller.currentSyllableIndex + 1}/{events.length} notes</strong></span>
          <span>Accuracy <strong>{accuracy}%</strong></span>
        </div>
      </div>

      {/* ── Piano ────────────────────────────────────────────────────── */}
      <div style={{
        borderTop: '1px solid var(--border-color, rgba(255,255,255,0.08))',
        background: 'var(--bg-card, #1a1a3e)',
        padding: '16px 0 24px',
      }}>

        {/* ── Adaptive toast ──────────────────────────────────────────── */}
        {adaptiveToast && (
          <div style={{
            margin: '0 28px 12px',
            padding: '10px 16px',
            background: 'rgba(139,92,246,0.15)',
            border: '1px solid rgba(139,92,246,0.35)',
            borderRadius: '10px',
            color: '#c4b5fd',
            fontSize: '0.85rem',
            fontWeight: 600,
            textAlign: 'center',
            animation: 'fadeIn 0.2s ease',
          }}>
            🎓 {adaptiveToast}
          </div>
        )}

        {/* ── Note result feedback flash ──────────────────────────────── */}
        {lastResult && (
          <div style={{
            margin: '0 28px 12px',
            padding: '10px 20px',
            borderRadius: '10px',
            fontWeight: 700,
            fontSize: '0.95rem',
            textAlign: 'center',
            transition: 'all 0.15s ease',
            ...(lastResult.result === 'correct'
              ? { background: 'rgba(34,197,94,0.15)', border: '1px solid rgba(34,197,94,0.4)', color: '#4ade80' }
              : lastResult.result === 'early' || lastResult.result === 'late'
              ? { background: 'rgba(245,158,11,0.15)', border: '1px solid rgba(245,158,11,0.4)', color: '#fbbf24' }
              : { background: 'rgba(239,68,68,0.15)', border: '1px solid rgba(239,68,68,0.4)', color: '#f87171' }),
          }}>
            {lastResult.result === 'correct' && '✓ Perfect'}
            {lastResult.result === 'early'   && `⏱ Too early — wait for the beat (${Math.abs(lastResult.timingDiffMs).toFixed(0)} ms early)`}
            {lastResult.result === 'late'    && `⏱ Too late (${Math.abs(lastResult.timingDiffMs).toFixed(0)} ms late)`}
            {lastResult.result === 'incorrect' && `✗ Expected ${lastResult.expectedPitch}`}
          </div>
        )}

        {/* ── Adaptive engine HUD ─────────────────────────────────────── */}
        {adaptiveState && (
          <div style={{
            margin: '0 28px 12px',
            display: 'flex',
            gap: '10px',
            justifyContent: 'flex-end',
            fontSize: '0.72rem',
            color: 'var(--text-secondary)',
          }}>
            <span style={{
              background: 'rgba(255,255,255,0.04)',
              border: '1px solid rgba(255,255,255,0.08)',
              borderRadius: '6px',
              padding: '3px 9px',
            }}>
              Tempo {adaptiveState.tempoMultiplier}x
            </span>
            <span style={{
              background: 'rgba(255,255,255,0.04)',
              border: '1px solid rgba(255,255,255,0.08)',
              borderRadius: '6px',
              padding: '3px 9px',
            }}>
              Hints: {adaptiveState.assistanceLevel > 0 ? `Level ${adaptiveState.assistanceLevel}` : 'Off'}
            </span>
          </div>
        )}

        {chordInfo && (
          <div style={{
            background: 'rgba(59, 130, 246, 0.1)',
            border: '1px solid rgba(59, 130, 246, 0.2)',
            borderRadius: '12px',
            padding: '12px 20px',
            margin: '0 28px 16px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            animation: 'fadeIn 0.3s ease',
          }}>
            <div>
              <span style={{ fontSize: '0.7rem', color: '#3b82f6', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Left Hand accompaniment</span>
              <h4 style={{ margin: '2px 0 0 0', fontSize: '1.1rem', fontWeight: 700 }}>🎹 Practice Chord: <span style={{ color: '#3b82f6' }}>{chordInfo.label}</span></h4>
            </div>
            <div style={{ display: 'flex', gap: '8px' }}>
              {chordInfo.keys.map(k => (
                <span key={k} style={{ background: '#1a1a3e', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '6px', padding: '4px 10px', fontSize: '0.8rem', fontWeight: 600 }}>{k}</span>
              ))}
            </div>
          </div>
        )}
        <PianoKeyboard
          highlightedNotes={pianoHighlights}
          onNotePlay={handleKeyPress}
        />
      </div>
    </div>
  );
};
