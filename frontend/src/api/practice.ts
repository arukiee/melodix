import { apiClient } from './client';

export type MissionType = 'listen' | 'right_hand' | 'left_hand' | 'both_hands' | 'tempo' | 'performance';
export type MissionStatus = 'locked' | 'available' | 'in_progress' | 'completed';

export interface ExpectedEvent {
  note: string;
  relative_time: number;
  duration: number;
}

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
}

export interface PracticePhase {
  id: string;
  title: string;
  missions: PracticeMission[];
}

export interface PracticeSessionResponse {
  lesson_id: string;
  overall_progress: number;
  phases: PracticePhase[];
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
  getLessonPractice: async (lessonId: string): Promise<PracticeSessionResponse> => {
    const response = await apiClient.get<PracticeSessionResponse>(`/api/v1/practice/lessons/${lessonId}`);
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
