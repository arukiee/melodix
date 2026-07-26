
import { useNavigate } from 'react-router-dom';
import { Flame, Sparkles, BookOpen, Music, Target } from 'lucide-react';
import { Button } from '../components/Button';
import { SongCard } from '../components/SongCard';
import { motion } from 'framer-motion';
import { useUser } from '../context/UserContext';
import styles from './Dashboard.module.css';

export function Dashboard() {
  const navigate = useNavigate();
  const { completedLessons, incrementLessons } = useUser();

  // Mock data for heatmap (52 weeks * 7 days)
  const heatmapData = Array.from({ length: 364 }).map(() => {
    return Math.random() > 0.6 ? Math.floor(Math.random() * 4) + 1 : 0;
  });

  const isNew = completedLessons === 0;

  // Development helper: Add a button to simulate completing a lesson
  const DevControls = () => (
    <div style={{ position: 'fixed', bottom: '24px', right: '24px', zIndex: 100, background: 'var(--bg-elevated)', padding: '16px', borderRadius: '8px', border: '1px solid var(--accent-primary)', display: 'flex', flexDirection: 'column', gap: '8px' }}>
      <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Dev Mode: {completedLessons} Lessons</div>
      <Button variant="primary" onClick={incrementLessons} style={{ padding: '8px' }}>Simulate Lesson</Button>
    </div>
  );

  return (
    <motion.div 
      className={styles.dashboard}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <DevControls />
      
      <header className={styles.header}>
        <h1 className={styles.greeting}>{isNew ? 'Welcome to Melodix!' : 'Good Afternoon, Sarah'}</h1>
        <div className={styles.date}>{isNew ? 'Your personalized learning journey is ready.' : 'Tuesday, Oct 24'}</div>
      </header>

      {isNew ? (
        <div className={styles.grid}>
          <div className={styles.continueSection}>
            <div className={styles.card} style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
              <h2 className={styles.cardTitle}>Today's Goal</h2>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', flex: 1, gap: '16px', textAlign: 'center', padding: '24px 0' }}>
                <div style={{ width: '80px', height: '80px', borderRadius: '50%', background: 'rgba(59, 130, 246, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Target size={40} color="var(--accent-primary)" />
                </div>
                <div>
                  <h3 style={{ fontSize: '24px', marginBottom: '8px' }}>Complete your first lesson</h3>
                  <p style={{ color: 'var(--text-secondary)' }}>Start your musical journey today.</p>
                </div>
              </div>
              <Button 
                variant="primary" 
                onClick={() => navigate('/song/c-major-scale')}
                style={{ width: '100%' }}
              >
                Start Learning
              </Button>
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            <div className={styles.card} style={{ flex: 1 }}>
              <h2 className={styles.cardTitle} style={{ marginBottom: '16px' }}>
                <BookOpen size={20} color="var(--accent-primary)" style={{ marginRight: '8px' }} />
                Learning Roadmap
              </h2>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '12px', background: 'var(--bg-elevated)', borderRadius: '8px' }}>
                  <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--accent-primary)' }} />
                  <span style={{ color: 'var(--text-primary)' }}>Finger Position</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '12px', background: 'var(--bg-elevated)', borderRadius: '8px' }}>
                  <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--border-color)' }} />
                  <span style={{ color: 'var(--text-secondary)' }}>C Major Scale</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '12px', background: 'var(--bg-elevated)', borderRadius: '8px' }}>
                  <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--border-color)' }} />
                  <span style={{ color: 'var(--text-secondary)' }}>Rhythm Exercise</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '12px', background: 'var(--bg-elevated)', borderRadius: '8px' }}>
                  <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--border-color)' }} />
                  <span style={{ color: 'var(--text-secondary)' }}>First Song</span>
                </div>
              </div>
            </div>

            <div className={`${styles.card} ${styles.aiPanel}`}>
              <h2 className={styles.cardTitle} style={{ color: 'var(--semantic-ai)' }}>
                <Sparkles size={20} /> AI Tip
              </h2>
              <p className={styles.aiText}>
                We’ll personalize every lesson as you practice. Complete your first lesson to unlock insights.
              </p>
            </div>
          </div>
        </div>
      ) : (
        <div className={styles.grid}>
          <div className={styles.continueSection}>
            <div className={styles.card}>
              <h2 className={styles.cardTitle}>Continue Learning</h2>
              <div className={styles.songHero}>
                <div style={{ width: '120px', height: '120px', borderRadius: '8px', background: 'linear-gradient(135deg, #121212, #1C1C1C)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                   <Music size={40} color="var(--text-muted)" />
                </div>
                <div className={styles.songInfo}>
                  <h3>C Major Scale</h3>
                  <p>Fundamentals • Beginner</p>
                  <div className={styles.progressBar}>
                    <div className={styles.progressFill} style={{ width: '15%' }}></div>
                  </div>
                  <div className={styles.progressText}>15% Complete</div>
                </div>
              </div>
              <Button 
                variant="primary" 
                onClick={() => navigate('/song/c-major-scale')}
                style={{ width: '100%' }}
              >
                Continue Practice
              </Button>
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            <div className={`${styles.card} ${styles.goalCard}`}>
              <h2 className={styles.cardTitle} style={{ justifyContent: 'center' }}>Today's Goal</h2>
              <div className={styles.goalCircle}>
                <svg width="120" height="120" viewBox="0 0 120 120">
                  <circle cx="60" cy="60" r="54" fill="none" stroke="var(--bg-elevated)" strokeWidth="8" />
                  <circle cx="60" cy="60" r="54" fill="none" stroke="var(--accent-primary)" strokeWidth="8" strokeDasharray="339" strokeDashoffset="250" strokeLinecap="round" style={{ transform: 'rotate(-90deg)', transformOrigin: '50% 50%' }} />
                </svg>
                <div className={styles.goalText}>8<span style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>/20</span></div>
              </div>
              <div className={styles.goalLabel}>minutes completed</div>
            </div>

            {completedLessons >= 7 && (
              <div className={`${styles.card} ${styles.aiPanel}`}>
                <h2 className={styles.cardTitle} style={{ color: 'var(--semantic-ai)' }}>
                  <Sparkles size={20} /> AI Recommendation
                </h2>
                <p className={styles.aiText}>
                  Yesterday you struggled with Measure 18. Practice it for 5 minutes before continuing.
                </p>
                <Button variant="secondary" onClick={() => navigate('/studio/moonlight-sonata')} style={{ background: 'rgba(59, 130, 246, 0.1)', color: 'var(--semantic-ai)', border: 'none' }}>
                  Practice Measure 18
                </Button>
              </div>
            )}
          </div>
        </div>
      )}

      {completedLessons >= 3 && (
        <section className={styles.section}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', margin: '48px 0 24px 0' }}>
            <h2 className={styles.cardTitle} style={{ marginBottom: 0 }}>Recently Practiced</h2>
            {completedLessons >= 3 && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--status-warning)', fontWeight: 600 }}>
                <Flame size={20} /> 3 Day Streak
              </div>
            )}
          </div>
          
          <div className={styles.recentGrid}>
            <SongCard 
              id="c-major-scale"
              title="C Major Scale"
              composer="Fundamentals"
              difficulty="Beginner"
              duration="5 min"
              progress={15}
              artworkUrl="" // Empty to show placeholder
            />
          </div>
        </section>
      )}

      {completedLessons >= 7 && (
        <section className={styles.section}>
          <h2 className={styles.cardTitle} style={{ marginTop: '48px' }}>Weekly Progress</h2>
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
        </section>
      )}
    </motion.div>
  );
}
