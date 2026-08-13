export interface LessonStep {
  id: string;
  title: string;
  type: 'listen' | 'watch' | 'play_hands_separate' | 'play_hands_together' | 'measure_practice';
  description: string;
  measures: number[];
  completed: boolean;
  locked: boolean;
}

export interface ProgressiveLesson {
  id: string;
  songTitle: string;
  steps: LessonStep[];
}

class LessonGenerator {
  generateLesson(songTitle: string, analysisData: any): ProgressiveLesson {
    const steps: LessonStep[] = [];
    
    // Step 1: Listen to the whole song
    steps.push({
      id: 'listen_full',
      title: 'Listen & Internalize',
      type: 'listen',
      description: 'Listen to the full arrangement to understand the rhythm and dynamics.',
      measures: [1, 2, 3, 4], // mock full
      completed: false,
      locked: false, // first step unlocked
    });

    // Step 2: Watch Animation
    steps.push({
      id: 'watch_intro',
      title: 'Watch the Intro',
      type: 'watch',
      description: 'Observe the finger placements and hand movements for the introduction.',
      measures: [1, 2],
      completed: false,
      locked: true,
    });

    // Step 3: Play Right Hand
    steps.push({
      id: 'play_rh',
      title: 'Play Right Hand',
      type: 'play_hands_separate',
      description: 'Play the melody with your right hand only.',
      measures: [1, 2],
      completed: false,
      locked: true,
    });

    // Step 4: Play Left Hand
    steps.push({
      id: 'play_lh',
      title: 'Play Left Hand',
      type: 'play_hands_separate',
      description: 'Play the accompaniment with your left hand only.',
      measures: [1, 2],
      completed: false,
      locked: true,
    });

    // Step 5: Hands Together
    steps.push({
      id: 'play_both',
      title: 'Hands Together',
      type: 'play_hands_together',
      description: 'Combine both hands and play the introduction slowly.',
      measures: [1, 2],
      completed: false,
      locked: true,
    });

    return {
      id: `lesson_${Date.now()}`,
      songTitle,
      steps
    };
  }

  unlockNextStep(lesson: ProgressiveLesson, completedStepId: string): ProgressiveLesson {
    const newLesson = { ...lesson, steps: [...lesson.steps] };
    const stepIndex = newLesson.steps.findIndex(s => s.id === completedStepId);
    
    if (stepIndex !== -1) {
      newLesson.steps[stepIndex].completed = true;
      if (stepIndex + 1 < newLesson.steps.length) {
        newLesson.steps[stepIndex + 1].locked = false;
      }
    }
    return newLesson;
  }
}

export const lessonGenerator = new LessonGenerator();
