import React, { useEffect, useState } from 'react';
import styles from './FeedbackOverlay.module.css';
import { Trophy, CheckCircle, XCircle } from 'lucide-react';

interface FeedbackOverlayProps {
  currentNote: string | null;
  expectedNote: string | null;
  score: number;
  accuracy: number;
  timing: number;
  showHighScore?: boolean;
}

export function FeedbackOverlay({
  currentNote,
  expectedNote,
  score,
  accuracy,
  timing,
  showHighScore
}: FeedbackOverlayProps) {
  const [feedbackState, setFeedbackState] = useState<'idle' | 'correct' | 'wrong'>('idle');

  useEffect(() => {
    if (!currentNote || !expectedNote) {
      setFeedbackState('idle');
      return;
    }

    if (currentNote === expectedNote) {
      setFeedbackState('correct');
    } else {
      setFeedbackState('wrong');
    }
    
    // Clear feedback state quickly for responsiveness
    const timeout = setTimeout(() => {
      setFeedbackState('idle');
    }, 800);
    
    return () => clearTimeout(timeout);
  }, [currentNote, expectedNote]);

  return (
    <div className={styles.overlay}>
      <div className={styles.topBar}>
        <div className={styles.metric}>
          <span className={styles.metricLabel}>Score</span>
          <span className={styles.metricValue}>{score}</span>
        </div>
        <div className={styles.metric}>
          <span className={styles.metricLabel}>Accuracy</span>
          <span className={styles.metricValue}>{Math.round(accuracy * 100)}%</span>
        </div>
        <div className={styles.metric}>
          <span className={styles.metricLabel}>Timing</span>
          <span className={styles.metricValue}>{Math.round(timing * 100)}%</span>
        </div>
      </div>

      <div className={styles.centerFeedback}>
        {feedbackState === 'correct' && (
          <div className={`${styles.feedbackMsg} ${styles.correctMsg}`}>
            <CheckCircle size={48} />
            <h2>Perfect!</h2>
          </div>
        )}
        {feedbackState === 'wrong' && (
          <div className={`${styles.feedbackMsg} ${styles.wrongMsg}`}>
            <XCircle size={48} />
            <h2>Expected {expectedNote}, got {currentNote}</h2>
          </div>
        )}
        {showHighScore && (
          <div className={`${styles.feedbackMsg} ${styles.highScoreMsg}`}>
            <Trophy size={48} />
            <h2>New High Score!</h2>
          </div>
        )}
      </div>
      
      <div className={styles.liveNoteArea}>
        <div className={styles.micStatus}>🎤 Listening...</div>
        <div className={styles.noteDisplay}>
          {currentNote ? (
            <span className={styles.detectedNote}>{currentNote}</span>
          ) : (
            <span className={styles.waiting}>Waiting for input...</span>
          )}
        </div>
      </div>
    </div>
  );
}
