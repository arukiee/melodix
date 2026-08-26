/**
 * PerformModeWorkspace — Level 7
 *
 * Full original arrangement at original BPM.
 * Both hands, scrolling double-rail note visualizer (Right Hand / Left Hand),
 * unified playhead line, dual-hand key lighting, and live recording/combo stats.
 */
import React, { useEffect, useRef, useState } from 'react';
import { Flame, Mic, Square, Play, Pause, RotateCcw } from 'lucide-react';
import type { PracticeMission, LyricAlignment } from '../../api/practice';
import { PianoKeyboard } from './PianoKeyboard';
import { LyricsHUD } from './LyricsHUD';
import { liveNoteDetector } from '../../services/liveNoteDetector';
import { usePlaybackController } from '../../services/usePlaybackController';

interface PerformModeWorkspaceProps {
  mission: PracticeMission;
  lyricAlignment: LyricAlignment | null | undefined;
  onComplete: () => void;
  onRequestAnalysis?: (blob: Blob) => void;
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

function notesMatch(a: string, b: string): boolean {
  const ma = noteToMidi(a), mb = noteToMidi(b);
  if (ma !== null && mb !== null) return ma === mb;
  return a.replace(/\d+$/, '').toUpperCase() === b.replace(/\d+$/, '').toUpperCase();
}

export const PerformModeWorkspace: React.FC<PerformModeWorkspaceProps> = ({
  mission,
  lyricAlignment,
  onComplete,
  onRequestAnalysis,
}) => {
  const events = mission.expectedEvents ?? [];

  const [combo, setCombo] = useState(0);
  const [maxCombo, setMaxCombo] = useState(0);
  const [correct, setCorrect] = useState(0);
  const [total, setTotal] = useState(0);
  const [isComplete, setIsComplete] = useState(false);
  const [isRecording, setIsRecording] = useState(false);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  // Initialize playback controller
  const controller = usePlaybackController(events, mission.bpm || 100, false);

  const accuracy = total > 0 ? Math.round((correct / total) * 100) : 100;

  // Live note detection matching during playback
  useEffect(() => {
    if (!controller.isPlaying) return;

    const unsub = liveNoteDetector.subscribe((note: string | null) => {
      if (!note) return;

      // Find if we are currently crossing any note in the events list
      const activeTargets = events.filter(
        e => controller.currentTime >= e.relative_time &&
             controller.currentTime <= (e.relative_time + e.duration)
      );

      if (activeTargets.length === 0) return;

      const hit = activeTargets.some(target => notesMatch(target.note, note));
      setTotal(t => t + 1);

      if (hit) {
        setCorrect(c => c + 1);
        setCombo(c => {
          const next = c + 1;
          setMaxCombo(m => Math.max(m, next));
          return next;
        });
      } else {
        setCombo(0);
      }
    });

    return unsub;
  }, [controller.isPlaying, controller.currentTime, events]);

  // Complete performance when playhead finishes
  useEffect(() => {
    if (controller.currentTime > 0 && controller.currentTime >= controller.duration) {
      handleStop();
      setIsComplete(true);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [controller.currentTime, controller.duration]);

  const handleStart = async () => {
    setCombo(0);
    setMaxCombo(0);
    setCorrect(0);
    setTotal(0);
    setIsComplete(false);

    // Start mic recording
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      liveNoteDetector.startListening();
      chunksRef.current = [];
      const mr = new MediaRecorder(stream);
      mr.ondataavailable = e => { if (e.data.size > 0) chunksRef.current.push(e.data); };
      mr.start(200);
      mediaRecorderRef.current = mr;
      setIsRecording(true);
    } catch { /* mic permission fallback */ }

    controller.startPlayback();
  };

  const handleStop = () => {
    controller.pausePlayback();
    if (mediaRecorderRef.current?.state === 'recording') {
      mediaRecorderRef.current.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/wav' });
        onRequestAnalysis?.(blob);
      };
      mediaRecorderRef.current.stop();
    }
    liveNoteDetector.stopListening();
    setIsRecording(false);
  };

  // Pixels per second for note rendering
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
          <span style={{ fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.12em', textTransform: 'uppercase', color: '#a855f7' }}>
            🟣 Level 7 — Perform
          </span>
          <div style={{ fontSize: '1rem', fontWeight: 600, marginTop: '2px' }}>{mission.title}</div>
        </div>

        {/* Stats bar */}
        <div style={{ display: 'flex', gap: '20px', fontSize: '0.85rem' }}>
          <span>
            Accuracy{' '}
            <strong style={{ color: accuracy >= 85 ? '#22c55e' : accuracy >= 65 ? '#f59e0b' : '#ef4444' }}>
              {accuracy}%
            </strong>
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <Flame size={14} style={{ color: combo >= 5 ? '#f97316' : '#6b7280' }} />
            <strong style={{ color: combo >= 5 ? '#f97316' : 'var(--text-primary, #fff)' }}>
              {combo}
            </strong>
          </span>
          <span>
            Tempo <strong>{mission.bpm?.toFixed(0)} BPM</strong>
          </span>
        </div>
      </div>

      {/* ── Lyrics HUD ───────────────────────────────────────────────── */}
      <div style={{ padding: '18px 28px 8px', textAlign: 'center' }}>
        <LyricsHUD lyricAlignment={lyricAlignment} currentSyllableIndex={controller.currentSyllableIndex} />
      </div>

      {/* ── Scrolling double-rail note visualizer ───────────────────── */}
      <div style={{
        flex: 1,
        padding: '12px 28px 20px',
        display: 'flex',
        flexDirection: 'column',
        gap: '20px',
        justifyContent: 'center',
      }}>
        {!controller.isPlaying && !isComplete ? (
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '3rem', marginBottom: '16px' }}>🟣</div>
            <h2 style={{ fontWeight: 800, fontSize: '1.6rem', margin: '0 0 8px' }}>Ready to Perform?</h2>
            <p style={{ color: 'var(--text-secondary, #9ca3af)', marginBottom: '28px' }}>
              Both hands · Original tempo · {events.length} notes
            </p>
            <button
              onClick={handleStart}
              style={{
                padding: '14px 40px',
                background: 'linear-gradient(135deg, #a855f7, #7c3aed)',
                color: '#fff',
                border: 'none',
                borderRadius: '100px',
                fontSize: '1.1rem',
                fontWeight: 700,
                cursor: 'pointer',
                boxShadow: '0 8px 32px #a855f740',
              }}
            >
              🎵 Start Performance
            </button>
          </div>
        ) : isComplete ? (
          <div style={{ textAlign: 'center', animation: 'fadeIn 0.4s ease' }}>
            <div style={{ fontSize: '3rem' }}>🎉</div>
            <h2 style={{ fontWeight: 800, fontSize: '1.6rem', marginBottom: '8px' }}>Performance Complete!</h2>
            <div style={{
              display: 'flex',
              gap: '24px',
              justifyContent: 'center',
              margin: '16px 0 28px',
              flexWrap: 'wrap',
            }}>
              {[
                { label: 'Accuracy', value: `${accuracy}%`, color: accuracy >= 85 ? '#22c55e' : '#f59e0b' },
                { label: 'Max Combo', value: `🔥 ${maxCombo}`, color: '#f97316' },
                { label: 'Notes Hit', value: `${correct}/${events.length}`, color: '#60a5fa' },
              ].map(({ label, value, color }) => (
                <div key={label} style={{
                  background: 'var(--bg-card, #1a1a3e)',
                  borderRadius: '12px',
                  padding: '14px 24px',
                  border: '1px solid var(--border-color, rgba(255,255,255,0.08))',
                  textAlign: 'center',
                }}>
                  <div style={{ fontSize: '1.4rem', fontWeight: 800, color }}>{value}</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary, #9ca3af)', marginTop: '4px' }}>{label}</div>
                </div>
              ))}
            </div>
            <button
              onClick={onComplete}
              style={{
                padding: '12px 32px',
                background: 'linear-gradient(135deg, #a855f7, #7c3aed)',
                color: '#fff',
                border: 'none',
                borderRadius: '100px',
                fontWeight: 700,
                cursor: 'pointer',
              }}
            >
              Finish →
            </button>
          </div>
        ) : (
          <>
            {/* Playback Controls Row */}
            <div style={{ display: 'flex', justifyContent: 'center', gap: '14px', alignItems: 'center', marginBottom: '8px' }}>
              <button
                onClick={controller.isPlaying ? controller.pausePlayback : controller.startPlayback}
                style={{
                  background: '#a855f7',
                  border: 'none',
                  color: '#fff',
                  width: '40px',
                  height: '40px',
                  borderRadius: '50%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  cursor: 'pointer',
                  boxShadow: '0 4px 12px rgba(168,85,247,0.3)',
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

            {/* Double-rail Scrolling Visualizer Container */}
            <div style={{
              position: 'relative',
              height: '200px',
              background: 'rgba(0,0,0,0.25)',
              borderRadius: '16px',
              border: '1px solid rgba(255,255,255,0.05)',
              overflow: 'hidden',
              boxShadow: 'inset 0 4px 20px rgba(0,0,0,0.4)',
              display: 'flex',
              flexDirection: 'column',
            }}>
              {/* Static Unified Playhead line in the center */}
              <div style={{
                position: 'absolute',
                left: `${playheadX}px`,
                top: 0,
                bottom: 0,
                width: '2px',
                background: 'linear-gradient(180deg, transparent, #a855f7, transparent)',
                boxShadow: '0 0 10px #a855f7',
                zIndex: 10,
              }} />

              {/* Top Rail: Right Hand */}
              <div style={{
                flex: 1,
                borderBottom: '1px dashed rgba(255,255,255,0.08)',
                position: 'relative',
              }}>
                <span style={{
                  position: 'absolute',
                  top: '6px',
                  left: '12px',
                  fontSize: '0.65rem',
                  fontWeight: 700,
                  color: '#a855f7',
                  opacity: 0.5,
                  textTransform: 'uppercase',
                }}>Right Hand Rail</span>

                {events.filter(e => e.hand !== 'left').map((e, idx) => {
                  const leftPos = playheadX + ((e.relative_time - controller.currentTime) * pxPerSec);
                  const width = Math.max(30, e.duration * pxPerSec);
                  const isCurrent = controller.currentTime >= e.relative_time && controller.currentTime <= e.relative_time + e.duration;
                  const isPast = controller.currentTime > e.relative_time + e.duration;

                  const midiNum = noteToMidi(e.note) || 60;
                  const row = (midiNum % 6) * 8; // distributed height in rail

                  return (
                    <div
                      key={idx}
                      style={{
                        position: 'absolute',
                        left: `${leftPos}px`,
                        top: `${20 + row}px`,
                        width: `${width}px`,
                        height: '18px',
                        background: isCurrent ? 'linear-gradient(135deg, #a855f7, #7c3aed)' : isPast ? 'rgba(255,255,255,0.03)' : 'rgba(168,85,247,0.35)',
                        border: isCurrent ? '1px solid #c084fc' : '1px solid rgba(255,255,255,0.05)',
                        borderRadius: '4px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '0.6rem',
                        fontWeight: 700,
                        color: isCurrent ? '#fff' : 'var(--text-secondary)',
                        boxShadow: isCurrent ? '0 0 12px rgba(168,85,247,0.6)' : 'none',
                        transition: 'left 0.1s linear',
                      }}
                    >
                      {e.note}
                    </div>
                  );
                })}
              </div>

              {/* Bottom Rail: Left Hand */}
              <div style={{
                flex: 1,
                position: 'relative',
              }}>
                <span style={{
                  position: 'absolute',
                  top: '6px',
                  left: '12px',
                  fontSize: '0.65rem',
                  fontWeight: 700,
                  color: '#60a5fa',
                  opacity: 0.5,
                  textTransform: 'uppercase',
                }}>Left Hand Rail</span>

                {events.filter(e => e.hand === 'left').map((e, idx) => {
                  const leftPos = playheadX + ((e.relative_time - controller.currentTime) * pxPerSec);
                  const width = Math.max(30, e.duration * pxPerSec);
                  const isCurrent = controller.currentTime >= e.relative_time && controller.currentTime <= e.relative_time + e.duration;
                  const isPast = controller.currentTime > e.relative_time + e.duration;

                  const midiNum = noteToMidi(e.note) || 60;
                  const row = (midiNum % 6) * 8;

                  return (
                    <div
                      key={idx}
                      style={{
                        position: 'absolute',
                        left: `${leftPos}px`,
                        top: `${20 + row}px`,
                        width: `${width}px`,
                        height: '18px',
                        background: isCurrent ? 'linear-gradient(135deg, #3b82f6, #1d4ed8)' : isPast ? 'rgba(255,255,255,0.03)' : 'rgba(59,130,246,0.35)',
                        border: isCurrent ? '1px solid #60a5fa' : '1px solid rgba(255,255,255,0.05)',
                        borderRadius: '4px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '0.6rem',
                        fontWeight: 700,
                        color: isCurrent ? '#fff' : 'var(--text-secondary)',
                        boxShadow: isCurrent ? '0 0 12px rgba(59,130,246,0.6)' : 'none',
                        transition: 'left 0.1s linear',
                      }}
                    >
                      {e.note}
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Stop button / recording log */}
            <div style={{ display: 'flex', justifyContent: 'center', gap: '16px' }}>
              <button
                onClick={handleStop}
                style={{
                  display: 'flex', alignItems: 'center', gap: '8px',
                  padding: '10px 24px',
                  background: '#ef4444',
                  color: '#fff',
                  border: 'none',
                  borderRadius: '100px',
                  fontWeight: 700,
                  cursor: 'pointer',
                }}
              >
                <Square size={14} />
                Stop Performance
              </button>
              {isRecording && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#ef4444', fontSize: '0.8rem' }}>
                  <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#ef4444', display: 'inline-block', animation: 'pulse 1s infinite' }} />
                  Recording Performance
                </div>
              )}
            </div>
          </>
        )}
      </div>

      {/* ── Piano Keyboard (Displays all active notes concurrently) ──── */}
      <div style={{
        borderTop: '1px solid var(--border-color, rgba(255,255,255,0.08))',
        background: 'var(--bg-card, #1a1a3e)',
        padding: '16px 0 24px',
      }}>
        <PianoKeyboard highlightedNotes={controller.activeNotes} onNotePlay={() => {}} />
      </div>
    </div>
  );
};
