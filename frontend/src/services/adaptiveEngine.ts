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
      targetBpm: this.targetBpm
    };
  }

  private notify() {
    this.onStateChange(this.getState());
  }
}
