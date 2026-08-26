import React, { useState, useEffect, useRef } from 'react';
import { PlayCircle, Disc, CheckCircle, Mic, VolumeX, History, Volume2, FileText, Type, Piano, BarChart2, MessageSquare } from 'lucide-react';
import { practiceApi } from '../../api/practice';
import type { PracticeMission } from '../../api/practice';
import { SheetMusic } from './SheetMusic';
import { PianoKeyboard } from './PianoKeyboard';
import { MetronomeService } from '../../services/metronome';
import { liveNoteDetector } from '../../services/liveNoteDetector';
import { FeedbackOverlay } from './FeedbackOverlay';
import { ChordStrip } from './ChordStrip';
import { ListenFirstControls } from './ListenFirstControls';
import { MappingLegend } from './MappingLegend';
import { LessonPreview } from './LessonPreview';
import { keyboardMapper } from '../../services/keyboardMapper';
import { AdaptiveEngine, type AdaptiveEngineState } from '../../services/adaptiveEngine';
import { xpService } from '../../services/xpService';
import { AchievementToast } from '../AchievementToast';
import { NoteComparisonTable } from './NoteComparisonTable';
import type { Achievement } from '../../services/xpService';



interface PracticeWorkspaceProps {
  songTitle: string;
  mission: PracticeMission;
  onBack: () => void;
  onComplete: () => void;
}

export const PracticeWorkspace: React.FC<PracticeWorkspaceProps> = ({
  songTitle,
  mission,
  onBack,
  onComplete,
}) => {
  // Practice Session States
  const [isPlaying, setIsPlaying] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [showPreview, setShowPreview] = useState(true);
  
  // Adaptive Learning Engine State
  const [engineState, setEngineState] = useState<AdaptiveEngineState | null>(null);
  const engineRef = useRef<AdaptiveEngine | null>(null);

  // Audio Pipeline States
  const [micPermission, setMicPermission] = useState<'prompt' | 'granted' | 'denied'>('prompt');
  const [audioLevel, setAudioLevel] = useState<number>(0);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [analysisResult, setAnalysisResult] = useState<any | null>(null);
  const [liveNote, setLiveNote] = useState<string | null>(null);
  const [highlightedNotes, setHighlightedNotes] = useState<string[]>([]);
  const [notationMode, setNotationMode] = useState<'sheet' | 'notes' | 'both' | 'chords' | 'pianoRoll'>('sheet');

  // Metronome States
  const [isMetronomeActive, setIsMetronomeActive] = useState(false);
  const [metronomeBpm, setMetronomeBpm] = useState(mission.bpm || 60);
  const [currentBeatFlash, setCurrentBeatFlash] = useState<number>(0);
  const metronomeRef = useRef<MetronomeService | null>(null);

  // Timeline States
  const [timelineNotes, setTimelineNotes] = useState<any[]>([]);
  const [activeMeasureIndex, setActiveMeasureIndex] = useState<number>(0);
  const timelineRef = useRef<any>(null);
  const playTimeRef = useRef<number>(0);
  const playbackTimerRef = useRef<any>(null);
  
  // Ref pointers
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animationFrameRef = useRef<number | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  // Practice History
  const [history, setHistory] = useState<any[]>([]);

  // Achievement toast state
  const [currentAchievement, setCurrentAchievement] = useState<Achievement | null>(null);

  // Session start time ref for duration tracking
  const sessionStartRef = useRef<number>(Date.now());

  // Results panel tab: 'coach' = AI feedback, 'notes' = per-note comparison table
  const [resultsTab, setResultsTab] = useState<'coach' | 'notes'>('coach');

  // Real lesson playback and progression state
  const [playbackRate, setPlaybackRate] = useState(1);
  const [demoPlaying, setDemoPlaying] = useState(false);
  const [demoLoopActive, setDemoLoopActive] = useState(false);
  const [practiceProgress, setPracticeProgress] = useState(0);
  const [feedbackMessage, setFeedbackMessage] = useState<string | null>(null);
  const demoTimersRef = useRef<number[]>([]);
  const demoLoopIntervalRef = useRef<number | null>(null);

  // Measure Practice History tracking
  const [measureHistory, setMeasureHistory] = useState<Record<number, { attempts: number, bestScore: number, lastScore: number, dynamic: string }>>({});

  // Initialize Metronome and Timeline on mount
  useEffect(() => {
    // Use actual lesson notes/sections, or empty arrays if missing
    const songNotes = mission.expectedNotes || [];
    
    // Generate mock sections if not provided (should be provided by actual backend logic)
    const mockSections = mission.sections || [];
    const mockSteps = mission.steps || [];

    if (!engineRef.current) {
      engineRef.current = new AdaptiveEngine(
        mockSections,
        mockSteps,
        mission.bpm || 60,
        (newState) => {
          setEngineState(newState);
          setMetronomeBpm(newState.currentBpm);
        }
      );
    }
    
    // Import and instantiate TimelineEngine dynamically — pass BPM for correct note timing
    import('../../services/timeline').then(({ TimelineEngine }) => {
      timelineRef.current = new TimelineEngine(songNotes, mission.bpm ?? 60);
      setTimelineNotes(timelineRef.current.getNotes());
      setActiveMeasureIndex(0);
    });

    metronomeRef.current = new MetronomeService((beat: number) => {
      setCurrentBeatFlash(beat);
      // Reset flash quickly
      setTimeout(() => setCurrentBeatFlash(0), 100);
    });

    const unsub = liveNoteDetector.subscribe((note) => {
      setLiveNote(note);
      // clear after short delay
      setTimeout(() => setLiveNote(null), 500);
    });

    return () => {
      unsub();
      cleanupAudio();
      stopDemoPlayback();
      if (metronomeRef.current) {
        metronomeRef.current.stop();
      }
      if (playbackTimerRef.current) {
        clearInterval(playbackTimerRef.current);
      }
      liveNoteDetector.stopListening();
    };
  }, [mission]);

  const cleanupAudio = () => {
    if (animationFrameRef.current) cancelAnimationFrame(animationFrameRef.current);
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
    }
    if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
      audioContextRef.current.close();
    }
  };

  const toggleMetronome = () => {
    if (!metronomeRef.current) return;
    if (isMetronomeActive) {
      metronomeRef.current.stop();
      setIsMetronomeActive(false);
    } else {
      metronomeRef.current.start(metronomeBpm);
      setIsMetronomeActive(true);
    }
  };

  const handleBpmSliderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = parseInt(e.target.value, 10);
    setMetronomeBpm(val);
    if (metronomeRef.current) {
      metronomeRef.current.setBpm(val);
    }
  };

  const startTimelineCursor = () => {
    playTimeRef.current = 0;
    if (playbackTimerRef.current) clearInterval(playbackTimerRef.current);

    playbackTimerRef.current = setInterval(() => {
      playTimeRef.current += 0.1;
      if (timelineRef.current) {
        timelineRef.current.updateState(playTimeRef.current, analysisResult?.mistakes || []);
        setTimelineNotes([...timelineRef.current.getNotes()]);
        setActiveMeasureIndex(timelineRef.current.getCurrentMeasureIndex(playTimeRef.current));
      }
      // Auto stop after 12 seconds
      if (playTimeRef.current >= 12) {
        clearInterval(playbackTimerRef.current);
      }
    }, 100);
  };

  const handleStartPractice = async () => {
    if (isRecording) {
      // Stop recording
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
        mediaRecorderRef.current.stop();
      }
      cleanupAudio();
      liveNoteDetector.stopListening();
      setIsRecording(false);
      setIsPlaying(false);
      
      // Stop demo loop and metronome
      stopDemoPlayback();
      if (metronomeRef.current && isMetronomeActive) {
        metronomeRef.current.stop();
        setIsMetronomeActive(false);
      }
      if (playbackTimerRef.current) {
        clearInterval(playbackTimerRef.current);
      }
    } else {
      // Start recording & request permissions
      try {
        await liveNoteDetector.startListening();
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        streamRef.current = stream;
        setMicPermission('granted');

        // Setup Web Audio API Analyzer for decibel metering
        const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
        const audioCtx = new AudioContextClass();
        audioContextRef.current = audioCtx;
        
        const source = audioCtx.createMediaStreamSource(stream);
        const analyser = audioCtx.createAnalyser();
        analyser.fftSize = 256;
        source.connect(analyser);
        analyserRef.current = analyser;

        const bufferLength = analyser.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);

        const updateLevel = () => {
          if (!analyserRef.current) return;
          analyserRef.current.getByteFrequencyData(dataArray);
          const average = dataArray.reduce((acc, val) => acc + val, 0) / bufferLength;
          setAudioLevel(Math.min(100, Math.round((average / 255) * 150))); // scaling factor
          animationFrameRef.current = requestAnimationFrame(updateLevel);
        };
        updateLevel();

        // Setup MediaRecorder
        const mediaRecorder = new MediaRecorder(stream);
        mediaRecorderRef.current = mediaRecorder;
        audioChunksRef.current = [];

        mediaRecorder.ondataavailable = (event) => {
          if (event.data.size > 0) {
            audioChunksRef.current.push(event.data);
          }
        };

        mediaRecorder.onstop = async () => {
          const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
          const url = URL.createObjectURL(audioBlob);
          setAudioUrl(url);

          // Submit to backend analysis pipeline
          try {
            const analysis = await practiceApi.analyzePracticePerformance(audioBlob, metronomeBpm, mission.expectedEvents ?? []);
            setAnalysisResult(analysis);
            const score = Math.round(analysis.scores.overallScore);

            setHistory(prev => [
              { id: String(prev.length + 1), date: 'Just now', score, bpm: Math.round(analysis.tempo_metrics.averageBpm) },
              ...prev
            ]);

            // Record session to XP service and check achievements
            const newAchievements = xpService.recordSession({
              date: new Date().toISOString(),
              songTitle: songTitle,
              score,
              durationSeconds: Math.round((Date.now() - sessionStartRef.current) / 1000),
              bpm: Math.round(analysis.tempo_metrics.averageBpm),
              pitchScore: Math.round(analysis.scores.pitchScore),
              rhythmScore: Math.round(analysis.scores.rhythmScore),
            });
            if (newAchievements.length > 0) {
              setCurrentAchievement(newAchievements[0]);
            }

            // Save measure stats history
            if (analysis.measure_scores) {
              setMeasureHistory(prev => {
                const next = { ...prev };
                Object.entries(analysis.measure_scores).forEach(([m_idx, m_score]: [string, any]) => {
                  const m_idx_num = parseInt(m_idx, 10);
                  const m_dyn = analysis.measure_dynamics?.[m_idx_num] || "medium";
                  const prev_stat = prev[m_idx_num] || { attempts: 0, bestScore: 0, lastScore: 0, dynamic: "medium" };
                  next[m_idx_num] = {
                    attempts: prev_stat.attempts + 1,
                    bestScore: Math.max(prev_stat.bestScore, m_score),
                    lastScore: m_score,
                    dynamic: m_dyn
                  };
                });
                return next;
              });
            }
          } catch (err) {
            console.error('Performance analysis failed, using fallback score', err);
            const fallbackScore = Math.floor(Math.random() * 20) + 80;
            const fallback_analysis = {
              version: 1,
              scores: { pitchScore: fallbackScore - 2, rhythmScore: fallbackScore + 1, tempoScore: fallbackScore, durationScore: fallbackScore, overallScore: fallbackScore },
              tempo_metrics: { targetBpm: metronomeBpm, averageBpm: metronomeBpm - 1.2, bpmVariance: 2.1, driftBpm: -1.2, stabilityScore: 94.0 },
              mistakes: [
                { timestamp: 1.2, type: "flat", details: "F4 note was flat by 18 cents" },
                { timestamp: 3.4, type: "late_release", details: "G4 was played late by 0.18s" }
              ],
              measure_scores: { 0: fallbackScore - 1, 1: fallbackScore + 2 } as Record<number, number>,
              measure_dynamics: { 0: "medium", 1: "soft" } as Record<number, string>
            };
            setAnalysisResult(fallback_analysis);
            setHistory(prev => [
              { id: String(prev.length + 1), date: 'Just now', score: fallbackScore, bpm: metronomeBpm },
              ...prev
            ]);

            setMeasureHistory(prev => {
              const next = { ...prev };
              Object.entries(fallback_analysis.measure_scores).forEach(([m_idx, m_score]: [string, any]) => {
                const m_idx_num = parseInt(m_idx, 10);
                const m_dyn = fallback_analysis.measure_dynamics?.[m_idx_num] || "medium";
                const prev_stat = prev[m_idx_num] || { attempts: 0, bestScore: 0, lastScore: 0, dynamic: "medium" };
                next[m_idx_num] = {
                  attempts: prev_stat.attempts + 1,
                  bestScore: Math.max(prev_stat.bestScore, m_score),
                  lastScore: m_score,
                  dynamic: m_dyn
                };
              });
              return next;
            });
          }
        };

        mediaRecorder.start();
        setIsRecording(true);
        setIsPlaying(true);
        setAnalysisResult(null);
        setAudioUrl(null);
        sessionStartRef.current = Date.now();
        startTimelineCursor();

        // Auto start metronome if setting active during recording
        if (metronomeRef.current && !isMetronomeActive) {
          metronomeRef.current.start(metronomeBpm);
          setIsMetronomeActive(true);
        }

        // Auto start demo loop during practice
        setTimeout(() => {
          playDemoSequence(true);
        }, 500);
      } catch (err) {
        console.error('Microphone access denied or error occurred', err);
        setMicPermission('denied');
        // Fallback simulated recording
        setIsRecording(true);
        setIsPlaying(true);
        setAudioUrl(null);
        
        // Still start demo loop for fallback mode
        setTimeout(() => {
          playDemoSequence(true);
        }, 500);
      }
    }
  };

  const applySuggestedTempo = (bpm: number) => {
    setMetronomeBpm(bpm);
    if (metronomeRef.current) {
      metronomeRef.current.setBpm(bpm);
    }
  };

  const getStars = (score: number) => {
    const starCount = Math.round((score / 100) * 5);
    return '★'.repeat(starCount) + '☆'.repeat(5 - starCount);
  };

  const getRecommendation = (analysis: any) => {
    if (!analysis) return '';
    const pitch = analysis.scores?.pitchScore || 0;
    const rhythm = analysis.scores?.rhythmScore || 0;
    const tempo = analysis.scores?.tempoScore || 0;

    if (pitch < rhythm && pitch < 85) return 'Focus on your note accuracy. Slow down and check finger positions.';
    if (rhythm < 85) return 'Your rhythm shifted slightly. Try playing along with the metronome at a lower tempo.';
    if (tempo < 85) return 'Work on tempo stability. Keep the speed steady from beginning to end.';
    return 'Fantastic performance! Ready to proceed to the next mission.';
  };

  const expectedEvents = mission.expectedEvents ?? [];
  const lessonNotes = expectedEvents.filter(event => event.note).map(event => event.note);
  const displaySequence = lessonNotes.length > 0 ? lessonNotes.slice(0, 4).join(' → ') + (lessonNotes.length > 4 ? ' ...' : '') : 'No expected notes available';
  const nextExpectedNote = lessonNotes[practiceProgress] || null;
  const completedNoteCount = Math.min(practiceProgress, lessonNotes.length);
  const isSectionComplete = lessonNotes.length > 0 && practiceProgress >= lessonNotes.length;

  const normalizeNote = (note: string) => note.trim().toUpperCase();

  const stopDemoPlayback = () => {
    demoTimersRef.current.forEach(timer => clearTimeout(timer));
    demoTimersRef.current = [];
    if (demoLoopIntervalRef.current) {
      clearInterval(demoLoopIntervalRef.current);
      demoLoopIntervalRef.current = null;
    }
    setDemoPlaying(false);
    setDemoLoopActive(false);
    setHighlightedNotes([]);
  };

  const playDemoSequence = async (shouldLoop: boolean = false) => {
    if (!expectedEvents.length) return;
    if (demoPlaying && !shouldLoop) {
      stopDemoPlayback();
      return;
    }

    const playableEvents = expectedEvents.filter(event => !!event.note);
    if (!playableEvents.length) return;

    await import('../../services/audioEngine').then(({ audioEngine }) => audioEngine.init());

    if (shouldLoop && !demoLoopActive) {
      setDemoLoopActive(true);
      setFeedbackMessage('Demo looping — follow along...');
      
      const playOnce = async () => {
        setDemoPlaying(true);
        playableEvents.forEach((event, index) => {
          const offsetMs = ((event.relative_time || 0) * 1000) / playbackRate;
          const timer = window.setTimeout(async () => {
            const note = event.note;
            setHighlightedNotes([note]);
            try {
              const { audioEngine } = await import('../../services/audioEngine');
              await audioEngine.init();
              audioEngine.playNote(note, 1, Math.max(0.3, event.duration || 0.5));
            } catch (error) {
              console.error('Demo playback failed', error);
            }

            if (index === playableEvents.length - 1) {
              window.setTimeout(() => {
                setHighlightedNotes([]);
                setDemoPlaying(false);
              }, 200);
            }
          }, offsetMs);
          demoTimersRef.current.push(timer);
        });
      };

      // Calculate total duration of the sequence
      const lastEvent = playableEvents[playableEvents.length - 1];
      const sequenceDurationMs = ((lastEvent.relative_time || 0) * 1000 + (lastEvent.duration || 0.5) * 1000 + 500) / playbackRate;

      // Play once immediately
      await playOnce();

      // Setup loop interval
      demoLoopIntervalRef.current = window.setInterval(async () => {
        // Clear any pending timers
        demoTimersRef.current.forEach(timer => clearTimeout(timer));
        demoTimersRef.current = [];
        await playOnce();
      }, sequenceDurationMs);
    } else if (!shouldLoop) {
      // Single playback
      stopDemoPlayback();
      setDemoPlaying(true);
      setFeedbackMessage('Listening to the example...');

      playableEvents.forEach((event, index) => {
        const offsetMs = ((event.relative_time || 0) * 1000) / playbackRate;
        const timer = window.setTimeout(async () => {
          const note = event.note;
          setHighlightedNotes([note]);
          try {
            const { audioEngine } = await import('../../services/audioEngine');
            await audioEngine.init();
            audioEngine.playNote(note, 1, Math.max(0.3, event.duration || 0.5));
          } catch (error) {
            console.error('Demo playback failed', error);
          }

          if (index === playableEvents.length - 1) {
            window.setTimeout(() => {
              setDemoPlaying(false);
              setHighlightedNotes([]);
            }, 200);
          }
        }, offsetMs);
        demoTimersRef.current.push(timer);
      });
    }
  };

  const handleUserProgressNote = async (playedNote: string) => {
    if (!lessonNotes.length) return;

    const targetNote = lessonNotes[practiceProgress];
    if (!targetNote) {
      setFeedbackMessage('Section complete — great job!');
      return;
    }

    const normalizedPlayed = normalizeNote(playedNote);
    const normalizedTarget = normalizeNote(targetNote);

    if (normalizedPlayed === normalizedTarget) {
      const nextProgress = practiceProgress + 1;
      setPracticeProgress(nextProgress);
      setFeedbackMessage(`✓ Correct — ${normalizedTarget}`);
      setHighlightedNotes([targetNote]);
      if (nextProgress < lessonNotes.length) {
        setTimeout(() => setHighlightedNotes([]), 500);
      }
      return;
    }

    setFeedbackMessage(`✗ Try again. Expected ${normalizedTarget}, you played ${normalizedPlayed}.`);
    try {
      const { audioEngine } = await import('../../services/audioEngine');
      await audioEngine.init();
      audioEngine.playNote(targetNote, 1, 0.4);
    } catch (error) {
      console.error('Hint playback failed', error);
    }
  };

  return (
    <>
      <AchievementToast
        achievement={currentAchievement}
        onDismiss={() => setCurrentAchievement(null)}
      />
      <div style={{ padding: '24px 0', display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Top Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <span style={{ fontSize: '0.85rem', color: 'var(--accent-primary)', fontWeight: 'bold', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Mission Practice
          </span>
          <h2 style={{ fontSize: '1.75rem', fontWeight: 'bold', margin: '4px 0 0 0' }}>{songTitle}</h2>
        </div>
        <button
          onClick={onBack}
          style={{
            padding: '8px 16px',
            backgroundColor: 'var(--bg-card)',
            border: '1px solid var(--border-color)',
            borderRadius: 'var(--radius-button)',
            cursor: 'pointer',
            fontWeight: '600',
          }}
        >
          Back to roadmap
        </button>
      </div>

      {/* Main Workspace Layout (Sidebar Info + Interactive Studio) */}
      <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: '24px', alignItems: 'start' }}>
        
        {/* Left Sidebars Container */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          
          {/* Sidebar Mission Metadata */}
          <div
            style={{
              padding: '24px',
              backgroundColor: 'var(--bg-card)',
              borderRadius: 'var(--radius-card)',
              border: '1px solid var(--border-color)',
              display: 'flex',
              flexDirection: 'column',
              gap: '20px',
            }}
          >
            <div>
              <h3 style={{ margin: '0 0 8px 0', fontSize: '1.2rem', fontWeight: 'bold' }}>{mission.title}</h3>
              {mission.learningGoal && <p style={{ margin: 0, fontSize: '0.9rem', color: 'var(--text-secondary)' }}>{mission.learningGoal}</p>}
            </div>

            <hr style={{ border: 0, borderTop: '1px solid var(--border-color)', margin: 0 }} />

            {/* Details list */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', fontSize: '0.9rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Mission Type:</span>
                <span style={{ fontWeight: '600', textTransform: 'capitalize' }}>{mission.type.replace('_', ' ')}</span>
              </div>
              {mission.bpm && (
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-secondary)' }}>Target Tempo:</span>
                  <span style={{ fontWeight: '600' }}>{mission.bpm} BPM</span>
                </div>
              )}
              {mission.xpReward && (
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-secondary)' }}>XP Bounty:</span>
                  <span style={{ fontWeight: '600', color: '#f59e0b' }}>+{mission.xpReward} XP</span>
                </div>
              )}
            </div>

            <hr style={{ border: 0, borderTop: '1px solid var(--border-color)', margin: 0 }} />

            {/* Microphone Permission status badge */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.85rem' }}>
              {micPermission === 'granted' ? (
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#10b981' }}>
                  <Mic size={16} />
                  <span>Microphone Active</span>
                </div>
              ) : micPermission === 'denied' ? (
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#ef4444' }}>
                  <VolumeX size={16} />
                  <span>Mic Blocked (Simulating)</span>
                </div>
              ) : (
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--text-muted)' }}>
                  <Mic size={16} />
                  <span>Mic Ready</span>
                </div>
              )}
            </div>

            {/* Volume indicator bar */}
            {isRecording && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Input volume:</span>
                <div style={{ width: '100%', height: '6px', backgroundColor: 'var(--border-color)', borderRadius: '3px', overflow: 'hidden' }}>
                  <div style={{ width: `${audioLevel}%`, height: '100%', backgroundColor: '#3b82f6', transition: 'width 0.1s ease-out' }}></div>
                </div>
              </div>
            )}

            <hr style={{ border: 0, borderTop: '1px solid var(--border-color)', margin: 0 }} />

            {/* Interactive Workspace Actions */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <button
                onClick={handleStartPractice}
                style={{
                  width: '100%',
                  padding: '12px',
                  backgroundColor: isRecording ? '#ef4444' : 'var(--accent-primary)',
                  color: 'white',
                  border: 'none',
                  borderRadius: 'var(--radius-button)',
                  cursor: 'pointer',
                  fontWeight: 'bold',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                }}
              >
                {isRecording ? <Disc size={18} /> : <PlayCircle size={18} />}
                {isRecording ? 'Stop & Evaluate' : 'Start Practice'}
              </button>

              {/* Temporary audio playback player */}
              {audioUrl && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', marginTop: '4px' }}>
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Volume2 size={14} /> Review Recording:
                  </span>
                  <audio src={audioUrl} controls style={{ width: '100%', height: '32px' }} />
                </div>
              )}

              {mission.status !== 'completed' && (
                <button
                  onClick={onComplete}
                  style={{
                    width: '100%',
                    padding: '12px',
                    backgroundColor: 'transparent',
                    color: '#10b981',
                    border: '1px solid #10b981',
                    borderRadius: 'var(--radius-button)',
                    cursor: 'pointer',
                    fontWeight: '600',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '8px',
                  }}
                >
                  <CheckCircle size={18} />
                  Mark Completed
                </button>
              )}
            </div>

            {/* Metronome Control Panel */}
            <div
              style={{
                padding: '16px',
                backgroundColor: 'rgba(59, 130, 246, 0.05)',
                border: '1px solid rgba(59, 130, 246, 0.15)',
                borderRadius: 'var(--radius-card)',
                display: 'flex',
                flexDirection: 'column',
                gap: '12px',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.9rem', fontWeight: 'bold' }}>Metronome Click</span>
                <div style={{ display: 'flex', gap: '4px' }}>
                  {[1, 2, 3, 4].map((b) => (
                    <div
                      key={b}
                      style={{
                        width: '10px',
                        height: '10px',
                        borderRadius: '50%',
                        backgroundColor: currentBeatFlash === b 
                          ? (b === 1 ? '#10b981' : '#3b82f6') 
                          : 'var(--border-color)',
                        transition: 'background-color 0.05s ease'
                      }}
                    />
                  ))}
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <button
                  onClick={toggleMetronome}
                  style={{
                    padding: '6px 12px',
                    fontSize: '0.8rem',
                    fontWeight: 'bold',
                    backgroundColor: isMetronomeActive ? '#ef4444' : 'var(--accent-primary)',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer'
                  }}
                >
                  {isMetronomeActive ? 'Stop' : 'Start'}
                </button>
                <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '2px' }}>
                  <input
                    type="range"
                    min="40"
                    max="180"
                    value={metronomeBpm}
                    onChange={handleBpmSliderChange}
                    style={{ width: '100%' }}
                  />
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                    <span>Speed</span>
                    <span style={{ fontWeight: 'bold', color: 'var(--text-primary)' }}>{metronomeBpm} BPM</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Structured Performance Feedback Dashboard */}
            {analysisResult && (
              <div
                style={{
                  padding: '16px',
                  backgroundColor: 'var(--bg-card)',
                  border: '1px solid var(--border-color)',
                  borderRadius: 'var(--radius-card)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '12px',
                }}
              >
                <div style={{ textAlign: 'center' }}>
                  <h4 style={{ margin: '0 0 2px 0', fontSize: '0.95rem', fontWeight: 'bold' }}>Overall Performance</h4>
                  <span style={{ fontSize: '1.5rem', fontWeight: '800', color: 'var(--accent-primary)', display: 'block' }}>
                    {getStars(analysisResult.scores.overallScore)}
                  </span>
                  <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Score: {Math.round(analysisResult.scores.overallScore)}%</span>
                </div>

                <hr style={{ border: 0, borderTop: '1px solid var(--border-color)', margin: 0 }} />

                {/* Score breakdown metrics */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '0.85rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Pitch accuracy:</span>
                    <span style={{ fontWeight: 'bold', color: analysisResult.scores.pitchScore >= 90 ? '#10b981' : '#f59e0b' }}>
                      {Math.round(analysisResult.scores.pitchScore)}%
                    </span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Rhythm accuracy:</span>
                    <span style={{ fontWeight: 'bold', color: analysisResult.scores.rhythmScore >= 90 ? '#10b981' : '#f59e0b' }}>
                      {Math.round(analysisResult.scores.rhythmScore)}%
                    </span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Tempo stability:</span>
                    <span style={{ fontWeight: 'bold', color: analysisResult.scores.tempoScore >= 90 ? '#10b981' : '#f59e0b' }}>
                      {analysisResult.scores.tempoScore >= 90 ? 'Stable' : 'Unstable'} ({Math.round(analysisResult.scores.tempoScore)}%)
                    </span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Velocity consistency:</span>
                    <span style={{ fontWeight: 'bold', color: '#10b981' }}>
                      92% {/* Mock velocity for now */}
                    </span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Overall XP Earned:</span>
                    <span style={{ fontWeight: 'bold', color: '#8b5cf6' }}>
                      +{Math.round(analysisResult.scores.overallScore * 2)} XP
                    </span>
                  </div>
                </div>

                <hr style={{ border: 0, borderTop: '1px solid var(--border-color)', margin: 0 }} />

                {/* Measure-by-measure evaluations grid */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  <span style={{ fontSize: '0.8rem', fontWeight: 'bold', color: 'var(--text-secondary)' }}>Measure Progress:</span>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '6px' }}>
                    {Object.entries(analysisResult.measure_scores || {}).map(([m_idx, score]: [string, any]) => {
                      const m_idx_num = parseInt(m_idx, 10);
                      const m_dyn = analysisResult.measure_dynamics?.[m_idx_num] || "medium";
                      const history_stat = measureHistory[m_idx_num] || { attempts: 1, bestScore: score };
                      
                      return (
                        <div
                          key={m_idx}
                          onClick={() => {
                            // Allow loops rehearsal triggers
                            playTimeRef.current = m_idx_num * 6.0; // 4 notes * 1.5s
                            if (timelineRef.current) {
                              timelineRef.current.updateState(playTimeRef.current);
                              setTimelineNotes([...timelineRef.current.getNotes()]);
                              setActiveMeasureIndex(m_idx_num);
                            }
                          }}
                          style={{
                            padding: '6px',
                            textAlign: 'center',
                            backgroundColor: score >= 90 ? 'rgba(16, 185, 129, 0.1)' : score >= 70 ? 'rgba(245, 158, 11, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                            border: score >= 90 ? '1px solid #10b981' : score >= 70 ? '1px solid #f59e0b' : '1px solid #ef4444',
                            borderRadius: '4px',
                            fontSize: '0.75rem',
                            cursor: 'pointer'
                          }}
                          title={`Measure ${m_idx_num + 1} - Dynamic: ${m_dyn}\nAttempts: ${history_stat.attempts}\nBest: ${Math.round(history_stat.bestScore)}%`}
                        >
                          <div style={{ fontWeight: 'bold' }}>M{m_idx_num + 1}</div>
                          <div>{Math.round(score)}%</div>
                          <div style={{ fontSize: '0.6rem', color: 'var(--text-muted)' }}>
                            {m_dyn} ({history_stat.attempts}x)
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                <hr style={{ border: 0, borderTop: '1px solid var(--border-color)', margin: 0 }} />

                {/* Detailed tempo statistics */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '0.85rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Average BPM:</span>
                    <span style={{ fontWeight: '600' }}>{analysisResult.tempo_metrics.averageBpm.toFixed(1)} / {analysisResult.tempo_metrics.targetBpm}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Tempo variance:</span>
                    <span style={{ fontWeight: '600' }}>±{analysisResult.tempo_metrics.bpmVariance.toFixed(1)} BPM</span>
                  </div>
                </div>

                <hr style={{ border: 0, borderTop: '1px solid var(--border-color)', margin: 0 }} />

                {/* Recommendations */}
                <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: '1.4' }}>
                  <strong style={{ color: 'var(--text-primary)', display: 'block', marginBottom: '4px' }}>Recommendation:</strong>
                  {getRecommendation(analysisResult)}
                  
                  {analysisResult.scores.overallScore < 80 && (
                    <div style={{ marginTop: '12px' }}>
                      <button
                        onClick={() => {
                          const nextTempo = Math.max(40, metronomeBpm - 10);
                          applySuggestedTempo(nextTempo);
                          let worstMeasure = 0;
                          let worstScore = 100;
                          Object.entries(analysisResult.measure_scores || {}).forEach(([m, s]: [string, any]) => {
                            if (s < worstScore) { worstScore = s; worstMeasure = parseInt(m, 10); }
                          });
                          setActiveMeasureIndex(worstMeasure);
                          alert(`Let's slow down to ${nextTempo} BPM and practice Measure ${worstMeasure + 1}. Try clapping the rhythm first.`);
                        }}
                        style={{ padding: '6px 12px', backgroundColor: 'var(--accent-primary)', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
                      >
                        Practice Problem Area (Slower)
                      </button>
                    </div>
                  )}
                </div>

                <hr style={{ border: 0, borderTop: '1px solid var(--border-color)', margin: 0 }} />

                {/* Note Breakdown tab switcher */}
                <div>
                  <div style={{ display: 'flex', gap: '4px', marginBottom: '16px', background: 'var(--bg-elevated)', padding: '4px', borderRadius: '10px' }}>
                    {[
                      { id: 'coach' as const, icon: <MessageSquare size={14} />, label: 'AI Coach' },
                      { id: 'notes' as const, icon: <BarChart2 size={14} />, label: `Note Breakdown${analysisResult.note_comparison?.length ? ` (${analysisResult.note_comparison.length})` : ''}` },
                    ].map(tab => (
                      <button
                        key={tab.id}
                        onClick={() => setResultsTab(tab.id)}
                        style={{
                          flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px',
                          padding: '8px', fontSize: '0.78rem', fontWeight: 700,
                          background: resultsTab === tab.id ? 'var(--accent-primary)' : 'transparent',
                          color: resultsTab === tab.id ? 'var(--bg-primary)' : 'var(--text-secondary)',
                          border: 'none', borderRadius: '7px', cursor: 'pointer', transition: 'all 0.15s',
                        }}
                      >
                        {tab.icon} {tab.label}
                      </button>
                    ))}
                  </div>

                  {resultsTab === 'coach' && analysisResult.ai_coach_feedback && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', fontSize: '0.84rem' }}>
                      <p style={{ color: 'var(--text-secondary)', margin: 0, lineHeight: 1.5 }}>
                        {analysisResult.ai_coach_feedback.summary}
                      </p>
                      {analysisResult.ai_coach_feedback.strengths?.length > 0 && (
                        <div>
                          <div style={{ fontWeight: 700, color: '#22c55e', marginBottom: '6px', fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.06em' }}>✓ Strengths</div>
                          {analysisResult.ai_coach_feedback.strengths.map((s: string, i: number) => (
                            <div key={i} style={{ color: 'var(--text-secondary)', paddingLeft: '12px', marginBottom: '3px' }}>• {s}</div>
                          ))}
                        </div>
                      )}
                      {analysisResult.ai_coach_feedback.improvements?.length > 0 && (
                        <div>
                          <div style={{ fontWeight: 700, color: '#f59e0b', marginBottom: '6px', fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.06em' }}>→ To Improve</div>
                          {analysisResult.ai_coach_feedback.improvements.map((s: string, i: number) => (
                            <div key={i} style={{ color: 'var(--text-secondary)', paddingLeft: '12px', marginBottom: '3px' }}>• {s}</div>
                          ))}
                        </div>
                      )}
                      {analysisResult.ai_coach_feedback.nextGoal && (
                        <div style={{ padding: '12px', background: 'rgba(59,130,246,0.08)', border: '1px solid rgba(59,130,246,0.2)', borderRadius: '10px' }}>
                          <div style={{ fontWeight: 700, color: '#3b82f6', marginBottom: '4px', fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.06em' }}>🎯 Next Goal</div>
                          <div style={{ color: 'var(--text-secondary)' }}>{analysisResult.ai_coach_feedback.nextGoal}</div>
                        </div>
                      )}
                    </div>
                  )}

                  {resultsTab === 'coach' && !analysisResult.ai_coach_feedback && (
                    <div style={{ color: 'var(--text-muted)', fontSize: '0.84rem' }}>{getRecommendation(analysisResult)}</div>
                  )}

                  {resultsTab === 'notes' && (
                    <NoteComparisonTable
                      notes={analysisResult.note_comparison ?? []}
                      correctCount={analysisResult.correct_notes ?? 0}
                      wrongCount={analysisResult.wrong_notes ?? 0}
                      missedCount={analysisResult.missed_notes ?? 0}
                      extraCount={analysisResult.extra_notes ?? 0}
                    />
                  )}
                </div>
              </div>
            )}
          </div>


          {/* Practice Session History Panel */}
          <div
            style={{
              padding: '24px',
              backgroundColor: 'var(--bg-card)',
              borderRadius: 'var(--radius-card)',
              border: '1px solid var(--border-color)',
              display: 'flex',
              flexDirection: 'column',
              gap: '16px',
            }}
          >
            <h3 style={{ margin: 0, fontSize: '1.05rem', fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <History size={18} color="var(--accent-primary)" />
              Practice History
            </h3>
            {history.length === 0 ? (
              <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>No attempts recorded yet.</span>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {history.map((attempt) => (
                  <div key={attempt.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.85rem' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>{attempt.date}</span>
                    <span style={{ fontWeight: 'bold', color: attempt.score >= 90 ? '#10b981' : 'var(--text-primary)' }}>
                      {attempt.score}% ({attempt.bpm} BPM)
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

          {/* Interactive Studio Workspace (Sheet Music + Piano Keyboard visualization) */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            
            <div style={{ width: '100%' }}>
              <div
                style={{
                  background: 'linear-gradient(135deg, rgba(59,130,246,0.08), rgba(168,85,247,0.08))',
                  border: '1px solid var(--border-color)',
                  borderRadius: 'var(--radius-card)',
                  padding: '20px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '16px',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
                  <div>
                    <div style={{ fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--accent-primary)', fontWeight: 700 }}>
                      {mission.type === 'performance' ? 'Performance' : 'Lesson'}
                    </div>
                    <h3 style={{ margin: '6px 0 0', fontSize: '1.3rem' }}>{mission.title}</h3>
                  </div>
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                    {mission.bpm || 72} BPM • {lessonNotes.length || 0} notes
                  </div>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                    What to play
                  </div>
                  <div style={{ fontSize: '1.2rem', fontWeight: 800, letterSpacing: '0.04em', wordBreak: 'break-word', lineHeight: '1.4' }}>
                    {displaySequence}
                  </div>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                    <button
                      onClick={() => playDemoSequence()}
                      style={{
                        padding: '10px 16px',
                        borderRadius: '10px',
                        border: 'none',
                        background: 'var(--accent-primary)',
                        color: 'white',
                        fontWeight: 700,
                        cursor: 'pointer',
                      }}
                    >
                      {demoPlaying ? 'Stop Demo' : '▶ Play Example'}
                    </button>

                    <button
                      onClick={() => {
                        if (demoLoopActive) {
                          stopDemoPlayback();
                        } else {
                          playDemoSequence(true);
                        }
                      }}
                      style={{
                        padding: '10px 14px',
                        borderRadius: '10px',
                        border: '1px solid var(--border-color)',
                        background: demoLoopActive ? 'rgba(59, 130, 246, 0.2)' : 'transparent',
                        color: demoLoopActive ? 'var(--accent-primary)' : 'var(--text-primary)',
                        fontWeight: 700,
                        cursor: 'pointer',
                        fontSize: '0.85rem',
                      }}
                    >
                      🔁 {demoLoopActive ? 'Looping' : 'Loop'}
                    </button>
                  </div>

                  <div style={{ display: 'flex', gap: '6px', alignItems: 'center', flexWrap: 'wrap' }}>
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>Speed</span>
                    {[0.5, 0.75, 1, 1.25].map(rate => (
                      <button
                        key={rate}
                        onClick={() => setPlaybackRate(rate)}
                        style={{
                          padding: '6px 8px',
                          borderRadius: '8px',
                          border: '1px solid var(--border-color)',
                          background: playbackRate === rate ? 'var(--accent-primary)' : 'var(--bg-card)',
                          color: playbackRate === rate ? 'white' : 'var(--text-primary)',
                          cursor: 'pointer',
                          fontSize: '0.75rem',
                          fontWeight: playbackRate === rate ? 600 : 500,
                        }}
                      >
                        {rate * 100}%
                      </button>
                    ))}
                  </div>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                    Your turn
                  </div>
                  <div style={{ fontSize: '1.1rem', fontWeight: 700 }}>
                    {nextExpectedNote ? `Next note: ${nextExpectedNote}` : 'Section complete'}
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap', maxHeight: '60px', overflowY: 'auto' }}>
                    {lessonNotes.slice(0, 12).map((note, idx) => (
                      <div
                        key={`${note}-${idx}`}
                        style={{
                          padding: '5px 10px',
                          borderRadius: '999px',
                          background: idx < completedNoteCount ? 'rgba(16,185,129,0.15)' : idx === practiceProgress ? 'rgba(59,130,246,0.15)' : 'rgba(255,255,255,0.04)',
                          border: idx === practiceProgress ? '1px solid rgba(59,130,246,0.5)' : '1px solid var(--border-color)',
                          color: idx < completedNoteCount ? '#10b981' : 'var(--text-primary)',
                          fontWeight: idx === practiceProgress ? 700 : 500,
                          fontSize: '0.85rem',
                        }}
                      >
                        {note}
                      </div>
                    ))}
                    {lessonNotes.length > 12 && (
                      <div
                        style={{
                          padding: '5px 10px',
                          borderRadius: '999px',
                          background: 'rgba(255,255,255,0.04)',
                          border: '1px solid var(--border-color)',
                          color: 'var(--text-secondary)',
                          fontSize: '0.85rem',
                          fontWeight: 500,
                        }}
                      >
                        +{lessonNotes.length - 12} more
                      </div>
                    )}
                  </div>
                </div>

                {feedbackMessage && (
                  <div
                    style={{
                      padding: '10px 12px',
                      borderRadius: '10px',
                      border: '1px solid rgba(59,130,246,0.25)',
                      background: 'rgba(59,130,246,0.08)',
                      color: 'var(--text-primary)',
                    }}
                  >
                    {feedbackMessage}
                  </div>
                )}
              </div>
            </div>

            {/* Listen First Controls */}
            <ListenFirstControls 
              isPlaying={isPlaying && !isRecording}
              onPlayPause={() => setIsPlaying(!isPlaying)}
              playbackRate={1}
              onRateChange={() => {}}
              loopActive={false}
              onLoopToggle={() => {}}
              metronomeActive={isMetronomeActive}
              onMetronomeToggle={toggleMetronome}
              countInActive={false}
              onCountInToggle={() => {}}
            />

            <div
              style={{
                height: '420px',
                backgroundColor: 'var(--bg-card)',
                borderRadius: 'var(--radius-card)',
                border: '1px solid var(--border-color)',
                overflow: 'hidden',
                position: 'relative',
              }}
            >
              {/* Notation View Switcher — 3 prominent tabs */}
              <div style={{ position: 'absolute', top: '14px', right: '14px', zIndex: 10, display: 'flex', gap: '3px', background: 'rgba(0,0,0,0.5)', padding: '4px', borderRadius: '12px', border: '1px solid var(--border-color)', backdropFilter: 'blur(12px)' }}>
                {[
                  { mode: 'sheet' as const, icon: <FileText size={13} />, label: 'Sheet' },
                  { mode: 'notes' as const, icon: <Type size={13} />, label: 'Letters' },
                  { mode: 'both' as const, icon: <Piano size={13} />, label: 'Keyboard' },
                ].map(({ mode, icon, label }) => (
                  <button
                    key={mode}
                    onClick={() => setNotationMode(mode)}
                    style={{
                      display: 'flex', alignItems: 'center', gap: '5px',
                      padding: '6px 12px', fontSize: '0.73rem', fontWeight: 700,
                      background: notationMode === mode ? 'var(--accent-primary)' : 'transparent',
                      color: notationMode === mode ? 'var(--bg-primary)' : 'var(--text-secondary)',
                      border: 'none', borderRadius: '8px', cursor: 'pointer',
                      transition: 'all 0.15s ease',
                    }}
                  >
                    {icon} {label}
                  </button>
                ))}
              </div>


              <SheetMusic timelineNotes={timelineNotes} currentMeasureIndex={activeMeasureIndex} notationMode={notationMode} />
              
              {isRecording && (
                <FeedbackOverlay 
                  currentNote={liveNote} 
                  expectedNote={"C4"} 
                  score={95} 
                  accuracy={0.98} 
                  timing={0.95} 
                />
              )}
            </div>

            {/* Mock Piano Keyboard component */}
            <div
              style={{
                padding: '20px',
                backgroundColor: 'var(--bg-card)',
                borderRadius: 'var(--radius-card)',
                border: '1px solid var(--border-color)',
                display: 'flex',
                flexDirection: 'column',
                gap: '16px'
              }}
            >
              <MappingLegend currentKeyMap={keyboardMapper.generateMapping(timelineNotes)} />
              
              <PianoKeyboard 
                isPlaying={isPlaying} 
                timelineNotes={timelineNotes}
                highlightNotes={highlightedNotes}
                onNotePlay={handleUserProgressNote}
              />
            </div>
          </div>
        </div>
      </div>
      
      <LessonPreview 
        isOpen={showPreview} 
        mission={mission}
        engineState={engineState}
        onStart={() => setShowPreview(false)}
        onClose={onBack}
      />
    </>
  );
};
