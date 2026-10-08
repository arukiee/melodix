// AdaptiveEngine.ts
// Handles the 12-stage adaptive learning sequence for a song section

export interface LessonSection {
  id: string;
  title: string;
  start_measure: number;
  end_measure: number;
}

export interface LessonStage {
  id: string;
  section_id: string;
  stage_id: number;
  name: string;
  type: 'listen' | 'watch' | 'interactive_single' | 'practice';
  tempo_pct: number;
  hand: 'right' | 'left' | 'both';
}

export interface AdaptiveEngineState {
  currentSectionIndex: number;
  currentStageIndex: number;
  activeSection: LessonSection | null;
  activeStage: LessonStage | null;
  isLooping: boolean;
  loopMeasure: number | null;
  currentBpm: number;
  targetBpm: number;
  // Live timing / adaptive feedback fields
  tempoMultiplier: number;
  assistanceLevel: number;
  lastAction: 'none' | 'slow_down' | 'add_assistance';
  actionMessage: string | null;
}

export class AdaptiveEngine {
  private sections: LessonSection[] = [];
  private steps: LessonStage[] = [];
  private targetBpm: number = 60;
  
  private currentSectionIndex = 0;
  private currentStageIndex = 0;
  
  private isLooping = false;
  private loopMeasure: number | null = null;
  
  private currentBpm = 60;

  // Per-note result tracking for live timing evaluation
  private noteResults: Array<{
    expectedPitch: number | null;
    playedPitch: number | null;
    timingDiffMs: number;
    result: string;
    timestamp: number;
  }> = [];
  private tempoMultiplier = 1.0;
  private assistanceLevel = 0;
  private lastAction: 'none' | 'slow_down' | 'add_assistance' = 'none';
  private actionMessage: string | null = null;

  private onStateChange: (state: AdaptiveEngineState) => void;

  constructor(
    sections: LessonSection[], 
    steps: LessonStage[], 
    targetBpm: number,
    onStateChange: (state: AdaptiveEngineState) => void
  ) {
    this.sections = sections;
    this.steps = steps;
    this.targetBpm = targetBpm;
    this.onStateChange = onStateChange;
    
    this.initializeState();
  }
  
  private initializeState() {
    if (this.sections.length > 0 && this.steps.length > 0) {
      this.currentSectionIndex = 0;
      this.currentStageIndex = 0;
      this.applyStageSettings();
    }
    this.notify();
  }
  
  private applyStageSettings() {
    const stage = this.getCurrentStage();
    if (stage) {
      this.currentBpm = Math.max(30, Math.round(this.targetBpm * (stage.tempo_pct / 100)));
    }
  }

  public getCurrentSection(): LessonSection | null {
    return this.sections[this.currentSectionIndex] || null;
  }
  
  public getCurrentStage(): LessonStage | null {
    return this.steps[this.currentStageIndex] || null;
  }
  
  public getStepsForSection(sectionId: string): LessonStage[] {
    return this.steps.filter(s => s.section_id === sectionId);
  }

  /**
   * Record a single note attempt from the live practice UI.
   * Tracks consecutive misses per expected pitch and triggers adaptive
   * responses (slow_down → add_assistance) after 2+ misses.
   */
  public recordNoteResult(payload: {
    expectedPitch: number | null;
    playedPitch: number | null;
    timingDiffMs: number;
    result: 'correct' | 'incorrect' | 'early' | 'late';
  }): void {
    this.noteResults.push({ ...payload, timestamp: Date.now() });
    this.lastAction = 'none';
    this.actionMessage = null;

    // On correct — reset and notify (no adaptive change needed)
    if (payload.result === 'correct') {
      this.notify();
      return;
    }

    // Count consecutive misses for this pitch in the last 6 attempts
    const recent = this.noteResults.slice(-6);
    const consecutiveMisses = recent.filter(
      r => r.expectedPitch === payload.expectedPitch && r.result !== 'correct'
    ).length;

    if (consecutiveMisses >= 2) {
      if (this.tempoMultiplier > 0.5) {
        this.tempoMultiplier = Math.round(Math.max(0.5, this.tempoMultiplier - 0.25) * 100) / 100;
        this.lastAction = 'slow_down';
        this.actionMessage = "Let's slow down. Watch this key.";
      } else {
        this.assistanceLevel = Math.min(2, this.assistanceLevel + 1);
        this.lastAction = 'add_assistance';
        this.actionMessage = 'Listen first, then play.';
      }
    }

    this.notify();
  }

  public getTempoMultiplier(): number {
    return this.tempoMultiplier;
  }

  public getAssistanceLevel(): number {
    return this.assistanceLevel;
  }

  public getNoteResults() {
    return [...this.noteResults];
  }

  public submitScore(score: number, recommendLoopMeasure: number | null, recommendTempoChange: number) {
    if (score >= 85) {
      // Pass! Move to next stage
      this.isLooping = false;
      this.loopMeasure = null;
      
      this.currentStageIndex++;
      
      // If we finished all stages, cap it. (Realistically we'd move to the next section)
      if (this.currentStageIndex >= this.steps.length) {
        this.currentStageIndex = this.steps.length - 1; 
      } else {
        const nextStage = this.getCurrentStage();
        if (nextStage && nextStage.section_id !== this.getCurrentSection()?.id) {
            // We moved to a new section!
            this.currentSectionIndex++;
        }
      }
      this.applyStageSettings();
    } else {
      // Failed. Apply recommendations
      if (recommendLoopMeasure !== null) {
        this.isLooping = true;
        this.loopMeasure = recommendLoopMeasure;
      }
      if (recommendTempoChange < 0) {
        this.currentBpm = Math.max(30, this.currentBpm + recommendTempoChange);
      }
    }
    this.notify();
  }
  
  public getActiveMeasureRange(): [number, number] {
      const section = this.getCurrentSection();
      if (!section) return [0, 1000];
      
      if (this.isLooping && this.loopMeasure !== null) {
          return [this.loopMeasure, this.loopMeasure + 1];
      }
      return [section.start_measure, section.end_measure];
  }
  
  public getState(): AdaptiveEngineState {
    return {
      currentSectionIndex: this.currentSectionIndex,
      currentStageIndex: this.currentStageIndex,
      activeSection: this.getCurrentSection(),
      activeStage: this.getCurrentStage(),
      isLooping: this.isLooping,
      loopMeasure: this.loopMeasure,
      currentBpm: this.currentBpm,
      targetBpm: this.targetBpm,
      tempoMultiplier: this.tempoMultiplier,
      assistanceLevel: this.assistanceLevel,
      lastAction: this.lastAction,
      actionMessage: this.actionMessage,
    };
  }

  private notify() {
    this.onStateChange(this.getState());
  }
}
