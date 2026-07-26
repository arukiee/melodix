import { Sparkles, Target, Activity } from 'lucide-react';
import styles from './AICoach.module.css';

export function AICoach() {
  return (
    <aside className={styles.container}>
      <div className={styles.header}>
        <Sparkles size={20} color="var(--semantic-ai)" />
        AI Coach
      </div>

      <div className={styles.goalCard}>
        <div className={styles.goalHeader}>
          <Target size={16} /> Today's Goal
        </div>
        <p className={styles.goalText}>
          Improve rhythm consistency in Measures 12–18.
        </p>
        <p className={styles.goalMeta}>Est. Time: 15 minutes</p>
      </div>

      <div className={styles.section}>
        <h3 className={styles.sectionTitle}>Live Feedback</h3>
        <div className={styles.feedbackCard}>
          Your rhythm remained steady through measures 1–8. Slow down to 80% tempo for measures 9–12 where timing became inconsistent.
        </div>
      </div>

      <div className={styles.section}>
        <h3 className={styles.sectionTitle}>Live Metrics</h3>
        <div className={styles.metricsGrid}>
          <div className={styles.metricBox}>
            <span className={styles.metricLabel}>Accuracy</span>
            <span className={`${styles.metricValue} ${styles.good}`}>94%</span>
          </div>
          <div className={styles.metricBox}>
            <span className={styles.metricLabel}>Rhythm</span>
            <span className={`${styles.metricValue} ${styles.warning}`}>82%</span>
          </div>
          <div className={styles.metricBox}>
            <span className={styles.metricLabel}>Tempo Stability</span>
            <span className={styles.metricValue}>88%</span>
          </div>
          <div className={styles.metricBox}>
            <span className={styles.metricLabel}>Expression</span>
            <span className={styles.metricValue}>90%</span>
          </div>
        </div>
      </div>

      <div className={styles.section}>
        <h3 className={styles.sectionTitle}>Mistakes Detected</h3>
        <ul className={styles.mistakeList}>
          <li><span className={styles.dot}></span> Rushed tempo in measure 11</li>
          <li><span className={styles.dot}></span> Missed C# in measure 14</li>
        </ul>
      </div>

      <div className={styles.section} style={{ marginTop: 'auto' }}>
        <h3 className={styles.sectionTitle}>Session Progress</h3>
        <div className={styles.progressCard}>
          <div className={styles.progressHeader}>
            <Activity size={16} /> 12m / 30m Goal
          </div>
          <div className={styles.progressBar}>
            <div className={styles.progressFill} style={{ width: '40%' }} />
          </div>
        </div>
      </div>
    </aside>
  );
}
