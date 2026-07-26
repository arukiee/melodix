import styles from './PracticeTimeline.module.css';

interface PracticeTimelineProps {
  playheadPos?: number;
}

export function PracticeTimeline({ playheadPos = 0 }: PracticeTimelineProps) {
  return (
    <div className={styles.container}>
      <div className={styles.track}>
        {/* Playhead */}
        <div className={styles.playhead} style={{ left: `${playheadPos}%` }} />
        
        {/* Practice Loop Zone */}
        <div className={styles.loopZone} style={{ left: '20%', width: '30%' }} />

        {/* Markers */}
        <div className={`${styles.marker} ${styles.mistake}`} style={{ left: '25%' }} title="Timing Mistake" />
        <div className={`${styles.marker} ${styles.mistake}`} style={{ left: '40%' }} title="Missed Note" />
        <div className={`${styles.marker} ${styles.bookmark}`} style={{ left: '60%' }} title="Chorus" />
        <div className={`${styles.marker} ${styles.ai}`} style={{ left: '75%' }} title="AI Suggestion" />
      </div>
      
      <div className={styles.labels}>
        <span>0:00</span>
        <span>Measure 12</span>
        <span>4:12</span>
      </div>
    </div>
  );
}
