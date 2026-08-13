import React, { useState } from 'react';
import styles from './LessonViewer.module.css';
import { Play, Eye, Hand, Users, CheckCircle, Lock } from 'lucide-react';
import type { ProgressiveLesson, LessonStep } from '../../services/lessonGenerator';

interface LessonViewerProps {
  lesson: ProgressiveLesson;
  onStepStart: (step: LessonStep) => void;
  onBack?: () => void;
}

export function LessonViewer({ lesson, onStepStart, onBack }: LessonViewerProps) {
  const getIconForType = (type: string) => {
    switch (type) {
      case 'listen': return <Play size={20} />;
      case 'watch': return <Eye size={20} />;
      case 'play_hands_separate': return <Hand size={20} />;
      case 'play_hands_together': return <Users size={20} />;
      default: return <Play size={20} />;
    }
  };

  return (
    <div className={styles.container}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '16px' }}>
        {onBack && (
          <button 
            onClick={onBack}
            style={{
              padding: '8px 16px',
              backgroundColor: 'var(--bg-secondary)',
              color: 'var(--text-primary)',
              border: '1px solid var(--border-color)',
              borderRadius: 'var(--radius-button)',
              cursor: 'pointer'
            }}
          >
            Back
          </button>
        )}
        <div>
          <h2 className={styles.title} style={{ margin: 0 }}>Practice: {lesson.songTitle}</h2>
          <p className={styles.subtitle} style={{ margin: 0 }}>Complete each step to unlock the next one.</p>
        </div>
      </div>
      
      <div className={styles.stepper}>
        {lesson.steps.map((step, idx) => (
          <div 
            key={step.id} 
            className={`${styles.stepCard} ${step.locked ? styles.locked : ''} ${step.completed ? styles.completed : ''}`}
          >
            <div className={styles.stepHeader}>
              <div className={styles.stepIconWrapper}>
                {step.completed ? <CheckCircle size={24} color="#10b981" /> : (step.locked ? <Lock size={20} /> : getIconForType(step.type))}
              </div>
              <div className={styles.stepInfo}>
                <h3>Step {idx + 1}: {step.title}</h3>
                <p>{step.description}</p>
                <div className={styles.measuresInfo}>
                  Measures: {step.measures.join(', ')}
                </div>
              </div>
              <div className={styles.stepAction}>
                <button 
                  className={styles.startBtn} 
                  disabled={step.locked}
                  onClick={() => onStepStart(step)}
                >
                  {step.completed ? 'Replay' : 'Start'}
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
