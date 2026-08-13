import React, { useState, useEffect } from 'react';
import { CheckCircle, Lock, Play, Star, ChevronDown, ChevronUp, Trophy } from 'lucide-react';
import styles from './PianoJourney.module.css';

export interface JourneyStep {
  id: string;
  title: string;
  description: string;
  type: 'listen' | 'watch' | 'right_hand' | 'left_hand' | 'both_hands' | 'performance';
  durationMin: number;
  xpReward: number;
}

export interface JourneyLevel {
  id: number;
  title: string;
  subtitle: string;
  emoji: string;
  color: string;
  steps: JourneyStep[];
}

const JOURNEY_LEVELS: JourneyLevel[] = [
  {
    id: 1,
    title: 'First Notes',
    subtitle: 'Meet your piano and play your first sounds',
    emoji: '🎹',
    color: '#22c55e',
    steps: [
      { id: 'l1-s1', title: 'Meet the Piano', description: 'Learn the layout of the keyboard and find Middle C', type: 'watch', durationMin: 5, xpReward: 20 },
      { id: 'l1-s2', title: 'Finger Numbers', description: 'Number your fingers 1–5 for both hands', type: 'watch', durationMin: 5, xpReward: 20 },
      { id: 'l1-s3', title: 'White Keys (C D E)', description: 'Play C, D, and E with your right hand', type: 'right_hand', durationMin: 10, xpReward: 30 },
      { id: 'l1-s4', title: 'Right Hand Melody', description: 'Play C–D–E–F–G in sequence with fingers 1–2–3–4–5', type: 'right_hand', durationMin: 10, xpReward: 40 },
      { id: 'l1-s5', title: 'Left Hand Melody', description: 'Mirror the pattern with your left hand', type: 'left_hand', durationMin: 10, xpReward: 40 },
      { id: 'l1-s6', title: 'First Song: Hot Cross Buns', description: 'Play your first complete song with the right hand', type: 'both_hands', durationMin: 15, xpReward: 60 },
    ],
  },
  {
    id: 2,
    title: 'Rhythm',
    subtitle: 'Feel the beat and stay in time',
    emoji: '🥁',
    color: '#3b82f6',
    steps: [
      { id: 'l2-s1', title: 'Listen: Quarter Notes', description: 'Hear what 4/4 time sounds like', type: 'listen', durationMin: 5, xpReward: 20 },
      { id: 'l2-s2', title: 'Clap the Beat', description: 'Clap quarter and half notes with the metronome', type: 'watch', durationMin: 5, xpReward: 20 },
      { id: 'l2-s3', title: 'Mary Had a Little Lamb', description: 'Simple melody with mixed note values', type: 'right_hand', durationMin: 15, xpReward: 50 },
      { id: 'l2-s4', title: 'Play with Metronome', description: 'Stay in time at 60 BPM', type: 'both_hands', durationMin: 15, xpReward: 60 },
    ],
  },
  {
    id: 3,
    title: 'Chords',
    subtitle: 'Add harmony — play two or more notes together',
    emoji: '🎵',
    color: '#a855f7',
    steps: [
      { id: 'l3-s1', title: 'What is a Chord?', description: 'Learn why chords make music feel full', type: 'listen', durationMin: 5, xpReward: 20 },
      { id: 'l3-s2', title: 'C Major Chord (C-E-G)', description: 'Press all three keys at once with fingers 1-3-5', type: 'right_hand', durationMin: 10, xpReward: 40 },
      { id: 'l3-s3', title: 'G Major Chord (G-B-D)', description: 'Learn your second chord', type: 'right_hand', durationMin: 10, xpReward: 40 },
      { id: 'l3-s4', title: 'F Major Chord (F-A-C)', description: 'Complete the I-IV-V progression', type: 'right_hand', durationMin: 10, xpReward: 40 },
      { id: 'l3-s5', title: 'Chord Switching', description: 'Smoothly switch between C–G–F–C', type: 'both_hands', durationMin: 15, xpReward: 60 },
    ],
  },
  {
    id: 4,
    title: 'Reading Music',
    subtitle: 'Decode the language of sheet music',
    emoji: '📄',
    color: '#f59e0b',
    steps: [
      { id: 'l4-s1', title: 'The Staff & Clef', description: 'What the lines mean and how to read them', type: 'watch', durationMin: 5, xpReward: 20 },
      { id: 'l4-s2', title: 'Treble Clef Notes', description: 'E-G-B-D-F and F-A-C-E — every good boy', type: 'watch', durationMin: 10, xpReward: 30 },
      { id: 'l4-s3', title: 'Bass Clef Notes', description: 'G-B-D-F-A and A-C-E-G — great big dogs', type: 'watch', durationMin: 10, xpReward: 30 },
      { id: 'l4-s4', title: 'Read & Play Simple Sheet', description: 'Follow sheet music for a 4-bar melody', type: 'right_hand', durationMin: 15, xpReward: 60 },
    ],
  },
  {
    id: 5,
    title: 'Easy Songs',
    subtitle: 'Real songs, simplified for beginners',
    emoji: '🎶',
    color: '#ec4899',
    steps: [
      { id: 'l5-s1', title: 'Twinkle Twinkle Little Star', description: 'Classic nursery rhyme, right hand melody', type: 'right_hand', durationMin: 15, xpReward: 60 },
      { id: 'l5-s2', title: 'Ode to Joy (Beethoven)', description: 'Simplified single-line melody', type: 'right_hand', durationMin: 15, xpReward: 60 },
      { id: 'l5-s3', title: 'Für Elise — Intro (8 bars)', description: 'The famous opening phrase, right hand only', type: 'right_hand', durationMin: 20, xpReward: 80 },
      { id: 'l5-s4', title: 'Add Left Hand Chords', description: 'Play melody + chord backing', type: 'both_hands', durationMin: 20, xpReward: 80 },
    ],
  },
  {
    id: 6,
    title: 'Intermediate Songs',
    subtitle: 'Full two-hand arrangements',
    emoji: '🏆',
    color: '#f97316',
    steps: [
      { id: 'l6-s1', title: 'River Flows In You — A Section', description: 'Yiruma — beautiful intro section', type: 'listen', durationMin: 5, xpReward: 20 },
      { id: 'l6-s2', title: 'Right Hand Only', description: 'Master the melody before adding left', type: 'right_hand', durationMin: 20, xpReward: 80 },
      { id: 'l6-s3', title: 'Left Hand Pattern', description: 'Arpeggiated chords in the bass', type: 'left_hand', durationMin: 20, xpReward: 80 },
      { id: 'l6-s4', title: 'Full Performance', description: 'Both hands together at full speed', type: 'both_hands', durationMin: 25, xpReward: 120 },
    ],
  },
  {
    id: 7,
    title: 'Advanced',
    subtitle: 'Challenge yourself with complex pieces',
    emoji: '🌟',
    color: '#ef4444',
    steps: [
      { id: 'l7-s1', title: 'Clair de Lune — Intro', description: 'Debussy — flowing triplets and dynamics', type: 'listen', durationMin: 5, xpReward: 20 },
      { id: 'l7-s2', title: 'Moonlight Sonata — Movement 1', description: 'Beethoven — iconic triplet arpeggios', type: 'listen', durationMin: 5, xpReward: 20 },
      { id: 'l7-s3', title: 'Canon in D', description: 'Pachelbel — layered harmonic progression', type: 'both_hands', durationMin: 30, xpReward: 150 },
      { id: 'l7-s4', title: 'Graduation Performance', description: 'Complete a piece from memory', type: 'performance', durationMin: 30, xpReward: 200 },
    ],
  },
];

// Progress key for localStorage
const PROGRESS_KEY = 'melodix_journey_progress';

interface JourneyProgress {
  completedSteps: string[];
  unlockedLevels: number[];
}

function loadProgress(): JourneyProgress {
  try {
    const raw = localStorage.getItem(PROGRESS_KEY);
    if (raw) return JSON.parse(raw);
  } catch {}
  return { completedSteps: ['l1-s1', 'l1-s2'], unlockedLevels: [1] };
}

function saveProgress(p: JourneyProgress) {
  localStorage.setItem(PROGRESS_KEY, JSON.stringify(p));
}

interface PianoJourneyProps {
  onStartStep: (level: JourneyLevel, step: JourneyStep) => void;
}

export function PianoJourney({ onStartStep }: PianoJourneyProps) {
  const [progress, setProgress] = useState<JourneyProgress>(loadProgress);
  const [expandedLevel, setExpandedLevel] = useState<number>(1);

  useEffect(() => {
    // Auto-expand lowest incomplete level
    const firstIncomplete = JOURNEY_LEVELS.find(l =>
      progress.unlockedLevels.includes(l.id) &&
      !l.steps.every(s => progress.completedSteps.includes(s.id))
    );
    if (firstIncomplete) setExpandedLevel(firstIncomplete.id);
  }, []);

  const isStepCompleted = (stepId: string) => progress.completedSteps.includes(stepId);

  const isStepUnlocked = (level: JourneyLevel, stepIdx: number) => {
    if (!progress.unlockedLevels.includes(level.id)) return false;
    if (stepIdx === 0) return true;
    return isStepCompleted(level.steps[stepIdx - 1].id);
  };

  const isLevelUnlocked = (levelId: number) => progress.unlockedLevels.includes(levelId);

  const getLevelProgress = (level: JourneyLevel) => {
    const completed = level.steps.filter(s => isStepCompleted(s.id)).length;
    return { completed, total: level.steps.length, pct: Math.round((completed / level.steps.length) * 100) };
  };

  const handleCompleteStep = (stepId: string, levelId: number, stepIdx: number, level: JourneyLevel) => {
    const newCompleted = [...new Set([...progress.completedSteps, stepId])];
    let newUnlocked = [...progress.unlockedLevels];
    // Unlock next level if all steps done
    if (stepIdx === level.steps.length - 1) {
      if (levelId < 7) newUnlocked = [...new Set([...newUnlocked, levelId + 1])];
    }
    const newProgress = { completedSteps: newCompleted, unlockedLevels: newUnlocked };
    setProgress(newProgress);
    saveProgress(newProgress);
  };

  const getStepTypeLabel = (type: string) => {
    switch (type) {
      case 'listen': return { label: '🎵 Listen', color: '#3b82f6' };
      case 'watch': return { label: '👁 Watch', color: '#8b5cf6' };
      case 'right_hand': return { label: '👉 Right Hand', color: '#f59e0b' };
      case 'left_hand': return { label: '👈 Left Hand', color: '#6366f1' };
      case 'both_hands': return { label: '🙌 Both Hands', color: '#10b981' };
      case 'performance': return { label: '🏆 Performance', color: '#ef4444' };
      default: return { label: type, color: '#888' };
    }
  };

  return (
    <div className={styles.journey}>
      <div className={styles.header}>
        <div className={styles.headerText}>
          <h1 className={styles.title}>🎹 Piano Journey</h1>
          <p className={styles.subtitle}>Your path from first notes to advanced pieces. Complete each step to unlock the next.</p>
        </div>
        <div className={styles.totalXP}>
          <Star size={16} color="#f59e0b" />
          <span>{progress.completedSteps.length * 40} XP earned</span>
        </div>
      </div>

      <div className={styles.levels}>
        {JOURNEY_LEVELS.map((level, levelIdx) => {
          const unlocked = isLevelUnlocked(level.id);
          const { completed, total, pct } = getLevelProgress(level);
          const isExpanded = expandedLevel === level.id;
          const isFullyComplete = completed === total;

          return (
            <div key={level.id} className={styles.levelWrapper}>
              {/* Connector line between levels */}
              {levelIdx > 0 && (
                <div
                  className={styles.connector}
                  style={{ borderColor: unlocked ? level.color : 'var(--border-color)' }}
                />
              )}

              <div
                className={`${styles.levelCard} ${!unlocked ? styles.locked : ''} ${isFullyComplete ? styles.complete : ''}`}
                style={{ '--level-color': level.color } as React.CSSProperties}
              >
                {/* Level Header */}
                <div
                  className={styles.levelHeader}
                  onClick={() => unlocked && setExpandedLevel(isExpanded ? 0 : level.id)}
                >
                  <div className={styles.levelLeft}>
                    <div
                      className={styles.levelBadge}
                      style={{ background: unlocked ? level.color : 'var(--bg-elevated)', border: `2px solid ${unlocked ? level.color : 'var(--border-color)'}` }}
                    >
                      {unlocked ? (
                        isFullyComplete ? <Trophy size={22} color="#fff" /> : <span className={styles.levelEmoji}>{level.emoji}</span>
                      ) : (
                        <Lock size={20} color="var(--text-muted)" />
                      )}
                    </div>
                    <div className={styles.levelInfo}>
                      <div className={styles.levelMeta}>
                        <span className={styles.levelNumber} style={{ color: unlocked ? level.color : 'var(--text-muted)' }}>
                          Level {level.id}
                        </span>
                        {isFullyComplete && <span className={styles.completeBadge}>✅ Complete</span>}
                        {!unlocked && <span className={styles.lockedBadge}>🔒 Locked</span>}
                      </div>
                      <h3 className={styles.levelTitle} style={{ color: unlocked ? 'var(--text-primary)' : 'var(--text-muted)' }}>
                        {level.title}
                      </h3>
                      <p className={styles.levelSubtitle}>{level.subtitle}</p>
                    </div>
                  </div>

                  <div className={styles.levelRight}>
                    {unlocked && (
                      <div className={styles.progressRing}>
                        <svg width="48" height="48" viewBox="0 0 48 48">
                          <circle cx="24" cy="24" r="20" fill="none" stroke="var(--bg-elevated)" strokeWidth="4" />
                          <circle
                            cx="24" cy="24" r="20" fill="none"
                            stroke={level.color} strokeWidth="4"
                            strokeDasharray={`${2 * Math.PI * 20}`}
                            strokeDashoffset={`${2 * Math.PI * 20 * (1 - pct / 100)}`}
                            strokeLinecap="round"
                            style={{ transform: 'rotate(-90deg)', transformOrigin: '50% 50%', transition: 'stroke-dashoffset 0.5s ease' }}
                          />
                        </svg>
                        <span className={styles.progressText}>{pct}%</span>
                      </div>
                    )}
                    {unlocked && (
                      <div className={styles.chevron}>
                        {isExpanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                      </div>
                    )}
                  </div>
                </div>

                {/* Progress bar */}
                {unlocked && (
                  <div className={styles.progressBar}>
                    <div
                      className={styles.progressFill}
                      style={{ width: `${pct}%`, background: level.color }}
                    />
                  </div>
                )}

                {/* Steps */}
                {unlocked && isExpanded && (
                  <div className={styles.steps}>
                    {level.steps.map((step, stepIdx) => {
                      const stepUnlocked = isStepUnlocked(level, stepIdx);
                      const stepCompleted = isStepCompleted(step.id);
                      const typeInfo = getStepTypeLabel(step.type);
                      const isCurrent = stepUnlocked && !stepCompleted;

                      return (
                        <div
                          key={step.id}
                          className={`${styles.stepRow} ${!stepUnlocked ? styles.stepLocked : ''} ${stepCompleted ? styles.stepDone : ''} ${isCurrent ? styles.stepCurrent : ''}`}
                          style={{ '--step-color': typeInfo.color } as React.CSSProperties}
                        >
                          <div className={styles.stepLeft}>
                            <div className={styles.stepStatus}>
                              {stepCompleted ? (
                                <CheckCircle size={22} color="#22c55e" />
                              ) : stepUnlocked ? (
                                <div className={styles.stepDot} style={{ background: typeInfo.color }} />
                              ) : (
                                <Lock size={16} color="var(--text-muted)" />
                              )}
                            </div>
                            <div className={styles.stepInfo}>
                              <div className={styles.stepMeta}>
                                <span className={styles.stepType} style={{ color: typeInfo.color, background: `${typeInfo.color}18` }}>
                                  {typeInfo.label}
                                </span>
                                <span className={styles.stepDuration}>{step.durationMin} min</span>
                              </div>
                              <h4 className={styles.stepTitle}>{step.title}</h4>
                              <p className={styles.stepDesc}>{step.description}</p>
                            </div>
                          </div>

                          <div className={styles.stepRight}>
                            <span className={styles.stepXP}>+{step.xpReward} XP</span>
                            {stepUnlocked && !stepCompleted && (
                              <button
                                className={styles.startBtn}
                                style={{ background: level.color }}
                                onClick={() => {
                                  onStartStep(level, step);
                                  // Mark complete after starting (will be properly tracked in PracticeWorkspace)
                                  handleCompleteStep(step.id, level.id, stepIdx, level);
                                }}
                              >
                                <Play size={14} />
                                Start
                              </button>
                            )}
                            {stepCompleted && (
                              <button
                                className={styles.replayBtn}
                                onClick={() => onStartStep(level, step)}
                              >
                                Replay
                              </button>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
