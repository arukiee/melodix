import { useEffect, useState } from 'react';
import { Sparkles, Target, Activity, Loader2 } from 'lucide-react';
import { apiClient } from '../../api/client';
import styles from './AICoach.module.css';

interface AICoachData {
  advice: string;
  goal: string;
  mistakes: string[];
  accuracy: number;
  rhythm_score: number;
  tempo_stability: number;
  expression_score: number;
}

export function AICoach() {
  const [coachData, setCoachData] = useState<AICoachData | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchAICoaching = async () => {
      setIsLoading(true);
      try {
        const { data } = await apiClient.post('/ai/coach', {
          song_title: 'Clair de Lune',
          accuracy: 94.0,
          rhythm_score: 82.0,
          difficulty: 'Advanced'
        });
        setCoachData(data);
      } catch (err) {
        console.error('Failed to fetch AI coaching:', err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchAICoaching();
  }, []);

  return (
    <aside className={styles.container}>
      <div className={styles.header}>
        <Sparkles size={20} color="var(--semantic-ai)" />
        AI Coach
      </div>

      {isLoading ? (
        <div style={{ textAlign: 'center', padding: '32px 0' }}>
          <Loader2 size={24} className="spin" color="var(--semantic-ai)" />
          <p style={{ fontSize: '12px', marginTop: '8px', color: 'var(--text-secondary)' }}>Analyzing performance...</p>
        </div>
      ) : (
        <>
          <div className={styles.goalCard}>
            <div className={styles.goalHeader}>
              <Target size={16} /> Today's Goal
            </div>
            <p className={styles.goalText}>
              {coachData?.goal || "Improve rhythm consistency in Measures 12–18."}
            </p>
            <p className={styles.goalMeta}>Est. Time: 15 minutes</p>
          </div>

          <div className={styles.section}>
            <h3 className={styles.sectionTitle}>Live Feedback</h3>
            <div className={styles.feedbackCard}>
              {coachData?.advice || "Your rhythm remained steady through measures 1–8. Slow down to 80% tempo for measures 9–12."}
            </div>
          </div>

          <div className={styles.section}>
            <h3 className={styles.sectionTitle}>Live Metrics</h3>
            <div className={styles.metricsGrid}>
              <div className={styles.metricBox}>
                <span className={styles.metricLabel}>Accuracy</span>
                <span className={`${styles.metricValue} ${styles.good}`}>
                  {coachData?.accuracy || 94}%
                </span>
              </div>
              <div className={styles.metricBox}>
                <span className={styles.metricLabel}>Rhythm</span>
                <span className={`${styles.metricValue} ${styles.warning}`}>
                  {coachData?.rhythm_score || 82}%
                </span>
              </div>
              <div className={styles.metricBox}>
                <span className={styles.metricLabel}>Tempo Stability</span>
                <span className={styles.metricValue}>
                  {coachData?.tempo_stability || 88}%
                </span>
              </div>
              <div className={styles.metricBox}>
                <span className={styles.metricLabel}>Expression</span>
                <span className={styles.metricValue}>
                  {coachData?.expression_score || 90}%
                </span>
              </div>
            </div>
          </div>

          <div className={styles.section}>
            <h3 className={styles.sectionTitle}>Mistakes Detected</h3>
            <ul className={styles.mistakeList}>
              {(coachData?.mistakes || ["Rushed tempo in measure 11", "Missed C# in measure 14"]).map((m, idx) => (
                <li key={idx}><span className={styles.dot}></span> {m}</li>
              ))}
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
        </>
      )}
    </aside>
  );
}
