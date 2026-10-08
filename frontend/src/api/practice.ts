import { apiClient } from './client';

export type MissionType =
  | 'listen' | 'right_hand' | 'left_hand' | 'both_hands'
  | 'tempo' | 'performance'
  | 'phrase_learn' | 'phrase_practice';  // Level 3 phrase loop missions

export type MissionStatus = 'locked' | 'available' | 'in_progress' | 'completed';

export interface ExpectedEvent {
  id?: string;            // optional stable ID for lyric-event linking
  note: string;
  relative_time: number;
  duration: number;
  hand?: 'right' | 'left';
}

// ---------------------------------------------------------------------------
// Lyric alignment types
// ---------------------------------------------------------------------------

/** How precisely lyrics were matched to notes. */
export type LyricAlignmentLevel = 'syllable' | 'word' | 'line' | 'none';

/** One syllable/word/line chunk aligned to one or more note events. */
export interface LyricSyllable {
  text: string;
  alignmentLevel: LyricAlignmentLevel;
  noteEventIds: string[];    // IDs of ExpectedEvents this chunk covers
  startTick?: number;
  endTick?: number;
}

/**
 * Song-level lyric alignment — stored once at the session level,
 * NOT duplicated inside every mission.
 */
export interface LyricAlignment {
  alignmentLevel: LyricAlignmentLevel;  // worst-case level across syllables
  confidence: number;                    // 0.0 – 1.0
  syllables: LyricSyllable[];
}

// ---------------------------------------------------------------------------
// Phrase types
// ---------------------------------------------------------------------------

/** Why a phrase boundary was placed here. */
export type PhraseBoundaryReason =
  | 'lyric_clause'    // syllable set ends with , . ? !
  | 'measure'         // measure number changed
  | 'rest'            // gap between notes > 0.3 s
  | 'long_note'       // note duration > 1.5× average
  | 'max_count';      // fallback: 8-note hard cap

/** A musically-bounded phrase ready for Listen / Watch / Play cycle. */
export interface SongPhrase {
  id: string;
  phraseIndex: number;
  phraseTotal: number;
  boundaryReason: PhraseBoundaryReason;
  expectedEvents: ExpectedEvent[];
  lyricSyllables?: LyricSyllable[];   // subset of song-level alignment
}

// ---------------------------------------------------------------------------
// Learning level types
// ---------------------------------------------------------------------------

export interface LearningLevel {
  id: string;
  levelNumber: number;          // 1–7
  title: string;
  learningMode: 'learn' | 'practice' | 'perform';
  handMode: 'right' | 'left' | 'both';
  progressionMode: 'wait' | 'timed';
  simplified: boolean;          // true for levels 5 & 6
  missions: PracticeMission[];
}

// ---------------------------------------------------------------------------
// Mission & session types (existing, extended)
// ---------------------------------------------------------------------------

export interface PracticeMission {
  id: string;
  title: string;
  type: MissionType;
  bpm?: number;
  status: MissionStatus;
  progress: number;
  learningGoal?: string;
  xpReward?: number;
  sections?: any[];
  steps?: any[];
  expectedNotes?: string[];
  expectedEvents?: ExpectedEvent[];
  // New progressive-learning fields
  levelNumber?: number;
  progressionMode?: 'wait' | 'timed';
  handMode?: 'right' | 'left' | 'both';
  phraseRef?: string;               // SongPhrase.id if phrase mission
  phraseIndex?: number;
  phraseTotal?: number;
  simplified?: boolean;
}

export interface PracticePhase {
  id: string;
  title: string;
  missions: PracticeMission[];
}

export interface PracticeSessionResponse {
  lesson_id: string;
  overall_progress: number;
  processing_job_id?: string;
  song_id?: string;
  current_mission_id?: string;
  phases: PracticePhase[];          // existing sidebar navigation
  // 5-level / 7-level progressive curriculum
  levels?: LearningLevel[];
  lyricAlignment?: LyricAlignment;  // song-level lyrics (not per-mission)
  phrases?: SongPhrase[];           // musically-bounded phrase list
}


export interface AnalysisMistake {
  timestamp: number;
  type: string;
  details: string;
}

/** One row in the per-note comparison table shown to the student after a session. */
export interface NoteComparisonEvent {
  expected_note: string;
  played_note: string | null;       // null = missed
  result: 'correct' | 'wrong' | 'missed' | 'extra';
  expected_time: number;
  played_time: number | null;
  timing_delta_ms: number | null;   // positive = late, negative = early
  expected_duration: number | null;
  played_duration: number | null;
  duration_delta_ms: number | null;
  cents_off: number | null;
}

export interface ScoreBreakdown {
  pitchScore: number;
  rhythmScore: number;
  tempoScore: number;
  durationScore: number;
  overallScore: number;
}

export interface TempoMetrics {
  targetBpm: number;
  averageBpm: number;
  bpmVariance: number;
  driftBpm: number;
  stabilityScore: number;
}

export interface AICoachFeedback {
  summary: string;
  strengths: string[];
  improvements: string[];
  nextGoal: string;
  recommend_loop_measure: number | null;
  recommend_tempo_change: number;
}

/** Full analysis response — all fields explicitly typed. */
export interface AnalysisResult {
  version: number;
  // Legacy flat fields (backward compat)
  noteAccuracy: number;
  rhythmAccuracy: number;
  tempoAccuracy: number;
  overallScore: number;
  detectedBpm: number;
  durationMs: number;
  mistakes: AnalysisMistake[];
  // Rich fields
  scores: ScoreBreakdown;
  tempo_metrics: TempoMetrics;
  ai_coach_feedback: AICoachFeedback | null;
  measure_scores: Record<string, number>;
  measure_dynamics: Record<string, string>;
  // Sprint 2.5 — per-note comparison
  note_comparison: NoteComparisonEvent[];
  correct_notes: number;
  wrong_notes: number;
  missed_notes: number;
  extra_notes: number;
}

export const practiceApi = {
  getSongPractice: async (songId: string): Promise<PracticeSessionResponse> => {
    const response = await apiClient.get<PracticeSessionResponse>(`/api/v1/practice/songs/${songId}`);
    return response.data;
  },

  submitSongMissionProgress: async (
    songId: string,
    missionId: string,
    status: MissionStatus,
    score?: number
  ): Promise<PracticeSessionResponse> => {
    const response = await apiClient.patch<PracticeSessionResponse>(
      `/api/v1/practice/songs/${songId}/missions/${missionId}`,
      { status, score }
    );
    return response.data;
  },

  getLessonPractice: async (lessonId: string): Promise<PracticeSessionResponse> => {
    const response = await apiClient.get<PracticeSessionResponse>(`/api/v1/practice/lessons/${lessonId}`);
    return response.data;
  },

  getJobPractice: async (jobId: string): Promise<PracticeSessionResponse> => {
    const response = await apiClient.get<PracticeSessionResponse>(`/api/v1/practice/jobs/${jobId}`);
    return response.data;
  },

  submitMissionProgress: async (
    lessonId: string,
    missionId: string,
    status: MissionStatus,
    score?: number
  ): Promise<PracticeSessionResponse> => {
    const response = await apiClient.patch<PracticeSessionResponse>(
      `/api/v1/practice/lessons/${lessonId}/missions/${missionId}`,
      { status, score }
    );
    return response.data;
  },

  submitJobMissionProgress: async (
    jobId: string,
    missionId: string,
    status: MissionStatus,
    score?: number
  ): Promise<PracticeSessionResponse> => {
    const response = await apiClient.patch<PracticeSessionResponse>(
      `/api/v1/practice/jobs/${jobId}/missions/${missionId}`,
      { status, score }
    );
    return response.data;
  },

  /**
   * Sends the recorded WAV blob + expected notes to the backend analyzer.
   * expectedNotes must be passed so the comparison engine knows what the student
   * was supposed to play — without it the comparison engine is blind.
   */
  analyzePracticePerformance: async (
    audioBlob: Blob,
    targetBpm: number,
    expectedEvents: ExpectedEvent[] = []
  ): Promise<AnalysisResult> => {
    const formData = new FormData();
    formData.append('file', audioBlob, 'performance.wav');
    formData.append('target_bpm', targetBpm.toString());
    
    // Send full ExpectedEvent structures as a JSON string so the backend has rich timing data
    formData.append('expected_events', JSON.stringify(expectedEvents));

    const response = await apiClient.post<AnalysisResult>('/api/v1/practice/analyze', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },
};
