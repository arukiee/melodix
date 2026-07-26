
import { useNavigate } from 'react-router-dom';
import { BarChart3, TrendingUp, Award, Zap, BookOpen, Sparkles, Play } from 'lucide-react';
import { motion } from 'framer-motion';
import { Button } from '../components/Button';
import { useUser } from '../context/UserContext';
import styles from './Progress.module.css';

export function Progress() {
  const navigate = useNavigate();
  const { completedLessons } = useUser();
  const isNew = completedLessons === 0;

  const mockChartData = [40, 60, 45, 80, 55, 90, 75];
  
  const heatmapData = Array.from({ length: 364 }).map(() => {
    return Math.random() > 0.6 ? Math.floor(Math.random() * 4) + 1 : 0;
  });

  return (
    <motion.div 
      className={styles.container}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <header className={styles.header}>
        <h1 className={styles.title}>Progress</h1>
        <p className={styles.subtitle}>Track your learning journey</p>
      </header>

      {isNew ? (
        <div style={{ textAlign: 'center', padding: '100px 0', background: 'var(--bg-card)', borderRadius: 'var(--radius-card)', border: '1px solid var(--border-color)', marginTop: '48px' }}>
          <BarChart3 size={48} color="var(--text-muted)" style={{ marginBottom: '24px' }} />
          <h2 className={styles.sectionTitle} style={{ marginBottom: '16px', justifyContent: 'center' }}>No practice sessions yet</h2>
          <p className={styles.subtitle} style={{ marginBottom: '32px', maxWidth: '400px', margin: '0 auto 32px' }}>
            Complete your first lesson to unlock Practice History, Accuracy Charts, AI Insights, Weekly Reports, and Streaks.
          </p>
          <Button variant="primary" onClick={() => navigate('/song/c-major-scale')} style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}>
            <Play size={16} /> Start First Lesson
          </Button>
        </div>
      ) : (
        <>
          {completedLessons >= 7 && (
            <div className={styles.aiInsights}>
              <div className={styles.aiHeader}>
                <Sparkles size={20} />
                AI Performance Insights
              </div>
              <p className={styles.aiText}>
                Your rhythm accuracy has improved by 15% this week. However, you're consistently rushing during allegro sections in classical pieces. Consider practicing with the metronome at 80% speed for your next 3 sessions.
              </p>
            </div>
          )}

          <div className={styles.section}>
            <h2 className={styles.sectionTitle}>Overview</h2>
            <div className={styles.grid}>
              <div className={styles.card}>
                <h3 className={styles.cardTitle}>
                  <TrendingUp size={20} color="var(--text-secondary)" />
                  Key Metrics
                </h3>
                <div className={styles.statsList}>
                  <div className={styles.statRow}>
                    <span className={styles.statLabel}>Current Streak</span>
                    <span className={styles.statValue}>{completedLessons >= 3 ? '3 Days' : '1 Day'}</span>
                  </div>
                  {completedLessons >= 3 && (
                    <div className={styles.statRow}>
                      <span className={styles.statLabel}>Longest Streak</span>
                      <span className={styles.statValue}>14 Days</span>
                    </div>
                  )}
                  <div className={styles.statRow}>
                    <span className={styles.statLabel}>Total Practice Time</span>
                    <span className={styles.statValue}>{completedLessons * 15}m</span>
                  </div>
                  <div className={styles.statRow}>
                    <span className={styles.statLabel}>Songs Mastered</span>
                    <span className={styles.statValue}>{Math.floor(completedLessons / 3)}</span>
                  </div>
                  <div className={styles.statRow}>
                    <span className={styles.statLabel}>Avg Accuracy</span>
                    <span className={styles.statValue}>91%</span>
                  </div>
                </div>
              </div>
              
              {completedLessons >= 3 && (
                <div className={styles.card}>
                  <h3 className={styles.cardTitle}>
                    <BarChart3 size={20} color="var(--text-secondary)" />
                    Practice Time (This Week)
                  </h3>
                  <div className={styles.chartPlaceholder}>
                    {mockChartData.map((val, i) => (
                      <div 
                        key={i} 
                        className={styles.bar} 
                        style={{ height: `${val}%` }}
                        title={`Day ${i + 1}`}
                      />
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {completedLessons >= 7 && (
            <div className={styles.section}>
              <h2 className={styles.sectionTitle}>Practice History</h2>
              <div className={styles.heatmapContainer}>
                <div className={styles.heatmapGrid}>
                  {heatmapData.map((level, i) => (
                    <div 
                      key={i} 
                      className={styles.heatmapCell} 
                      data-level={level}
                      title={`Practice session ${i}`}
                    />
                  ))}
                </div>
              </div>
            </div>
          )}

          {completedLessons >= 3 && (
            <div className={styles.section}>
              <h2 className={styles.sectionTitle}>Recent Achievements</h2>
              <div className={styles.achievementsGrid}>
                {completedLessons >= 7 && (
                  <div className={styles.achievementCard}>
                    <div className={styles.achievementIcon}><Zap size={24} /></div>
                    <div className={styles.achievementInfo}>
                      <span className={styles.achievementName}>10 Day Streak</span>
                      <span className={styles.achievementDate}>2 days ago</span>
                    </div>
                  </div>
                )}
                <div className={styles.achievementCard}>
                  <div className={styles.achievementIcon}><Award size={24} /></div>
                  <div className={styles.achievementInfo}>
                    <span className={styles.achievementName}>Perfect Accuracy</span>
                    <span className={styles.achievementDate}>1 week ago</span>
                  </div>
                </div>
                <div className={styles.achievementCard}>
                  <div className={styles.achievementIcon}><BookOpen size={24} /></div>
                  <div className={styles.achievementInfo}>
                    <span className={styles.achievementName}>First Song Mastered</span>
                    <span className={styles.achievementDate}>2 weeks ago</span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </motion.div>
  );
}
