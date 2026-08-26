/**
 * PracticeModeWorkspace — Levels 3, 4, 5, 6
 *
 * Implements:
 * 1. A central playback loop using `usePlaybackController` to sync audio + visuals.
 * 2. Listen & Watch tabs: Auto-advancing playhead with audio synthesizer & virtual keyboard highlighting.
 * 3. Play tab: Interactive practice where correct note keystroke advances current note.
 * 4. A clean, Synthesia-style horizontal scrolling note visualizer with a fixed Playhead bar.
 */
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Headphones, Eye, Play, Pause, RotateCcw } from 'lucide-react';
import type { PracticeMission, LyricAlignment, SongPhrase } from '../../api/practice';
import { PianoKeyboard } from './PianoKeyboard';
import { LyricsHUD } from './LyricsHUD';
import { usePlaybackController } from '../../services/usePlaybackController';

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

  // Initialize playback controller
  // In 'listen' and 'watch' modes we auto-synthesize notes
  const isAutoPlay = phraseTab === 'listen' || phraseTab === 'watch' || !isPhrase;
  const controller = usePlaybackController(events, mission.bpm || 60, isAutoPlay);

  // Reset play session states on tab switch or mission changes
  useEffect(() => {
    controller.stopPlayback();
    setPlayIndex(0);
    setAttempts(0);
    setCorrectCount(0);
    setAccuracy(100);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [phraseTab, mission.id]);

  // Handle keys hit on play tab
  const handleKeyPress = (note: string) => {
    if (phraseTab !== 'play' && isPhrase) return;

    const targetNote = events[playIndex];
    if (!targetNote) return;

    setAttempts(a => a + 1);
    const isCorrect = noteToMidi(note) === noteToMidi(targetNote.note);

    if (isCorrect) {
      setCorrectCount(c => c + 1);
      const nextIdx = playIndex + 1;
      if (nextIdx >= events.length) {
        setPlayIndex(events.length);
        // Complete the mission
        setTimeout(() => onComplete(), 800);
      } else {
        setPlayIndex(nextIdx);
      }
    }

    setAccuracy(Math.round(((correctCount + (isCorrect ? 1 : 0)) / (attempts + 1)) * 100));
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
