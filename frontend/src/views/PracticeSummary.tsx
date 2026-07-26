import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Check, Target, Clock, Activity, Play, Star, ChevronRight, MessageSquare } from 'lucide-react';
import { Button } from '../components/Button';
import styles from './PracticeSummary.module.css';

export function PracticeSummary() {
  const navigate = useNavigate();

  return (
    <div className={styles.container}>
      <motion.div 
        className={styles.content}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <div className={styles.header}>
          <div className={styles.badge}>Session Complete</div>
          <h1 className={styles.title}>Great practice today!</h1>
          <p className={styles.subtitle}>You completed <strong>Clair de Lune</strong> and achieved your daily goal.</p>
        </div>

        <div className={styles.grid}>
          {/* Main Stats */}
          <div className={`${styles.card} ${styles.primaryCard}`}>
            <h3 className={styles.cardTitle}>Performance Overview</h3>
            <div className={styles.statsRow}>
              <div className={styles.statBox}>
                <span className={styles.statLabel}>Accuracy</span>
                <span className={styles.statValue} style={{ color: 'var(--status-success)' }}>94%</span>
              </div>
              <div className={styles.statBox}>
                <span className={styles.statLabel}>Rhythm</span>
                <span className={styles.statValue}>88%</span>
              </div>
              <div className={styles.statBox}>
                <span className={styles.statLabel}>Time</span>
                <span className={styles.statValue}>12:45</span>
              </div>
              <div className={styles.statBox}>
                <span className={styles.statLabel}>XP Gained</span>
                <span className={styles.statValue} style={{ color: 'var(--accent-primary)' }}>+150</span>
              </div>
            </div>
            
            <div className={styles.sectionDivider} />

            <h4 className={styles.subTitle}>Section Analysis</h4>
            <div className={styles.analysisRow}>
              <div className={styles.analysisItem}>
                <span className={styles.analysisIcon} style={{ color: 'var(--status-success)' }}><Star size={16} /></span>
                <div>
                  <div className={styles.analysisLabel}>Strongest Section</div>
                  <div className={styles.analysisText}>Measures 1–8 (98% Accuracy)</div>
                </div>
              </div>
              <div className={styles.analysisItem}>
                <span className={styles.analysisIcon} style={{ color: 'var(--status-warning)' }}><Target size={16} /></span>
                <div>
                  <div className={styles.analysisLabel}>Needs Focus</div>
                  <div className={styles.analysisText}>Measures 12–16 (Rhythm slips)</div>
                </div>
              </div>
            </div>
          </div>

          {/* AI Summary */}
          <div className={`${styles.card} ${styles.aiCard}`}>
            <h3 className={styles.cardTitle}>
              <MessageSquare size={18} style={{ color: 'var(--semantic-ai)' }} /> 
              AI Feedback
            </h3>
            <p className={styles.aiText}>
              "You've made significant progress on the phrasing in the first page. Your dynamic control is improving, but be careful not to rush the tempo during the arpeggios in measure 14. Tomorrow, let's focus on isolating the left hand in that section."
            </p>
          </div>

          {/* Next Steps */}
          <div className={`${styles.card} ${styles.nextCard}`}>
            <h3 className={styles.cardTitle}>Up Next</h3>
            <div className={styles.nextItem}>
              <div className={styles.nextInfo}>
                <div className={styles.nextLabel}>Recommended Exercise</div>
                <div className={styles.nextTitle}>Left Hand Arpeggio Drill</div>
              </div>
              <Button variant="secondary" style={{ padding: '8px 16px', fontSize: '12px' }}>
                Start <Play size={12} style={{ marginLeft: '4px' }} />
              </Button>
            </div>
          </div>
        </div>

        <div className={styles.actions}>
          <Button variant="ghost" onClick={() => navigate('/studio')}>
            Practice Again
          </Button>
          <Button variant="primary" onClick={() => navigate('/dashboard')}>
            Return to Dashboard <ChevronRight size={16} style={{ marginLeft: '4px' }} />
          </Button>
        </div>
      </motion.div>
    </div>
  );
}
