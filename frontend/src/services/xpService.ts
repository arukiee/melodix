/* XP Service — localStorage-based XP and achievement tracking */

export interface Achievement {
  id: string;
  title: string;
  description: string;
  emoji: string;
  xpReward: number;
  unlockedAt?: string;
}

export interface XPState {
  totalXP: number;
  streak: number;
  lastPracticeDate: string | null;
  sessions: SessionRecord[];
  achievements: string[]; // achievement IDs
  practiceMinutesToday: number;
}

export interface SessionRecord {
  id: string;
  date: string;
  songTitle: string;
  score: number;
  durationSeconds: number;
  bpm: number;
  pitchScore: number;
  rhythmScore: number;
}

const XP_KEY = 'melodix_xp_state';

const ACHIEVEMENTS: Achievement[] = [
  { id: 'first_note', title: 'First Note!', description: 'Completed your very first lesson step', emoji: '🎵', xpReward: 50 },
  { id: 'perfect_rhythm', title: 'Perfect Rhythm', description: 'Scored 100% on rhythm in a session', emoji: '🎯', xpReward: 100 },
  { id: 'no_mistakes', title: 'No Mistakes', description: 'Completed a session with 0 pitch errors', emoji: '⭐', xpReward: 150 },
  { id: 'streak_3', title: '3-Day Streak', description: 'Practiced 3 days in a row', emoji: '🔥', xpReward: 75 },
  { id: 'streak_7', title: '7-Day Streak', description: 'Practiced 7 days in a row', emoji: '🔥🔥', xpReward: 200 },
  { id: 'level_2', title: 'Level Up!', description: 'Unlocked Level 2 — Rhythm', emoji: '🚀', xpReward: 100 },
  { id: 'level_3', title: 'Chord Master', description: 'Unlocked Level 3 — Chords', emoji: '🎸', xpReward: 100 },
  { id: 'left_hand_master', title: 'Left Hand Master', description: 'Completed all left-hand missions', emoji: '🎹', xpReward: 120 },
  { id: 'session_5', title: 'Committed', description: 'Completed 5 practice sessions', emoji: '💪', xpReward: 80 },
  { id: 'session_20', title: 'Dedicated', description: 'Completed 20 practice sessions', emoji: '🏅', xpReward: 200 },
  { id: 'score_90', title: 'High Achiever', description: 'Scored 90%+ in any session', emoji: '🌟', xpReward: 100 },
];

function defaultState(): XPState {
  return {
    totalXP: 0,
    streak: 0,
    lastPracticeDate: null,
    sessions: [],
    achievements: [],
    practiceMinutesToday: 0,
  };
}

function loadState(): XPState {
  try {
    const raw = localStorage.getItem(XP_KEY);
    if (raw) return { ...defaultState(), ...JSON.parse(raw) };
  } catch {}
  return defaultState();
}

function saveState(state: XPState) {
  localStorage.setItem(XP_KEY, JSON.stringify(state));
}

function getLevel(xp: number): number {
  if (xp < 200) return 1;
  if (xp < 500) return 2;
  if (xp < 1000) return 3;
  if (xp < 2000) return 4;
  if (xp < 3500) return 5;
  if (xp < 5000) return 6;
  return 7;
}

function getLevelTitle(level: number): string {
  const titles = ['', 'Beginner', 'Novice', 'Learner', 'Intermediate', 'Advanced', 'Expert', 'Maestro'];
  return titles[level] || 'Maestro';
}

function getXPForNextLevel(xp: number): { current: number; needed: number; levelXP: number } {
  const thresholds = [0, 200, 500, 1000, 2000, 3500, 5000, Infinity];
  const level = getLevel(xp);
  const current = xp - thresholds[level - 1];
  const needed = thresholds[level] - thresholds[level - 1];
  return { current, needed, levelXP: thresholds[level - 1] };
}

class XPService {
  getState(): XPState {
    return loadState();
  }

  addXP(amount: number, reason: string): { newlyUnlocked: Achievement[] } {
    const state = loadState();
    state.totalXP += amount;
    saveState(state);
    console.log(`[XP] +${amount} XP (${reason}) → Total: ${state.totalXP}`);
    return { newlyUnlocked: [] };
  }

  recordSession(session: Omit<SessionRecord, 'id'>): Achievement[] {
    const state = loadState();
    const newSession: SessionRecord = { ...session, id: Date.now().toString() };
    state.sessions = [newSession, ...state.sessions.slice(0, 49)]; // keep last 50

    // Update streak
    const today = new Date().toDateString();
    if (state.lastPracticeDate !== today) {
      const yesterday = new Date(Date.now() - 86400000).toDateString();
      if (state.lastPracticeDate === yesterday) {
        state.streak += 1;
      } else if (state.lastPracticeDate !== today) {
        state.streak = 1;
      }
      state.lastPracticeDate = today;
    }

    // Add XP from session score
    const xpEarned = Math.round(session.score * 1.5);
    state.totalXP += xpEarned;

    // Check achievements
    const newlyUnlocked: Achievement[] = [];
    const check = (id: string, condition: boolean) => {
      if (condition && !state.achievements.includes(id)) {
        const ach = ACHIEVEMENTS.find(a => a.id === id);
        if (ach) {
          state.achievements.push(id);
          state.totalXP += ach.xpReward;
          newlyUnlocked.push(ach);
        }
      }
    };

    check('first_note', state.sessions.length >= 1);
    check('session_5', state.sessions.length >= 5);
    check('session_20', state.sessions.length >= 20);
    check('score_90', session.score >= 90);
    check('perfect_rhythm', session.rhythmScore >= 99);
    check('no_mistakes', session.pitchScore >= 99);
    check('streak_3', state.streak >= 3);
    check('streak_7', state.streak >= 7);

    saveState(state);
    return newlyUnlocked;
  }

  getLevel(): number { return getLevel(loadState().totalXP); }
  getLevelTitle(): string { return getLevelTitle(this.getLevel()); }
  getProgressToNextLevel() { return getXPForNextLevel(loadState().totalXP); }
  getStreak(): number { return loadState().streak; }
  getRecentSessions(n = 10): SessionRecord[] { return loadState().sessions.slice(0, n); }
  getTotalXP(): number { return loadState().totalXP; }
  getAllAchievements(): Achievement[] { return ACHIEVEMENTS; }
  getUnlockedAchievements(): Achievement[] {
    const state = loadState();
    return ACHIEVEMENTS.filter(a => state.achievements.includes(a.id));
  }
  getTotalPracticeMinutes(): number {
    const state = loadState();
    return Math.round(state.sessions.reduce((acc, s) => acc + s.durationSeconds, 0) / 60);
  }
}

export const xpService = new XPService();
