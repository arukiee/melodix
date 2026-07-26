import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Plus, MessageSquare, Play, Calendar, Star, TrendingUp, TrendingDown, Check } from 'lucide-react';
import { motion } from 'framer-motion';
import { Button } from '../components/Button';
import styles from './StudentDetail.module.css';

export function StudentDetail() {
  const { id } = useParams();
  const navigate = useNavigate();

  // Mock data based on id
  const student = {
    id: id,
    name: 'Sarah Jenkins',
    avatar: 'S',
    level: 'Intermediate',
    joinDate: 'Sept 2025',
    lastActive: '2 hrs ago',
    stats: {
      practiceTime: '24.5 hrs',
      accuracy: '94%',
      assignmentsCompleted: 12
    }
  };

  return (
    <motion.div 
      className={styles.container}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
    >
      <header className={styles.header}>
        <div className={styles.headerLeft}>
          <button className={styles.backBtn} onClick={() => navigate(-1)}>
            <ArrowLeft size={20} />
          </button>
          <div className={styles.avatarLg}>{student.avatar}</div>
          <div>
            <h1 className={styles.name}>{student.name}</h1>
            <p className={styles.meta}>
              {student.level} • Joined {student.joinDate} • Last active {student.lastActive}
            </p>
          </div>
        </div>
        <div className={styles.headerActions}>
          <Button variant="secondary" onClick={() => alert('Opening message thread...')}>
            <MessageSquare size={16} style={{ marginRight: '8px' }} />
            Message
          </Button>
          <Button variant="primary" onClick={() => alert('Assigning lesson...')}>
            <Plus size={16} style={{ marginRight: '8px' }} />
            Assign Lesson
          </Button>
        </div>
      </header>

      <div className={styles.statsGrid}>
        <div className={styles.statCard}>
          <div className={styles.statHeader}>Total Practice Time</div>
          <div className={styles.statValue}>{student.stats.practiceTime}</div>
          <div className={styles.statTrend} style={{ color: 'var(--status-success)' }}>
            <TrendingUp size={14} /> +2.4 hrs this week
          </div>
        </div>
        <div className={styles.statCard}>
          <div className={styles.statHeader}>Average Accuracy</div>
          <div className={styles.statValue}>{student.stats.accuracy}</div>
          <div className={styles.statTrend} style={{ color: 'var(--status-warning)' }}>
            <TrendingDown size={14} /> -1% this week
          </div>
        </div>
        <div className={styles.statCard}>
          <div className={styles.statHeader}>Assignments</div>
          <div className={styles.statValue}>{student.stats.assignmentsCompleted}</div>
          <div className={styles.statTrend} style={{ color: 'var(--status-success)' }}>
            <Star size={14} /> All caught up
          </div>
        </div>
      </div>

      <div className={styles.layout}>
        <div className={styles.mainCol}>
          <section className={styles.section}>
            <h2 className={styles.sectionTitle}>Recent Activity</h2>
            <div className={styles.activityList}>
              <div className={styles.activityItem}>
                <div className={styles.activityIcon}><Play size={16} /></div>
                <div className={styles.activityContent}>
                  <div className={styles.activityTitle}>Practiced Clair de Lune</div>
                  <div className={styles.activityMeta}>Today • 45 mins • 96% Accuracy</div>
                </div>
                <Button variant="ghost" style={{ padding: '4px 12px', fontSize: '12px' }}>Review</Button>
              </div>
              <div className={styles.activityItem}>
                <div className={styles.activityIcon} style={{ background: 'var(--status-success)', color: '#000' }}><Check size={16} /></div>
                <div className={styles.activityContent}>
                  <div className={styles.activityTitle}>Completed Assignment: Scales</div>
                  <div className={styles.activityMeta}>Yesterday • 100% Accuracy</div>
                </div>
              </div>
            </div>
          </section>

          <section className={styles.section}>
            <h2 className={styles.sectionTitle}>AI Analytics Breakdown</h2>
            <div className={styles.card}>
              <div className={styles.aiInsight}>
                <strong>Rhythm Analysis:</strong> Sarah consistently rushes measures 14-20. Recommend assigning a metronome-enforced drill at 80bpm.
              </div>
              <div className={styles.aiInsight}>
                <strong>Expression:</strong> Dynamic range is improving, but pedaling remains muddy in the transition sections.
              </div>
            </div>
          </section>
        </div>

        <div className={styles.sideCol}>
          <section className={styles.section}>
            <h2 className={styles.sectionTitle}>Teacher Notes</h2>
            <div className={styles.card}>
              <textarea 
                className={styles.notesArea} 
                placeholder="Add private notes about Sarah's progress..."
                defaultValue="Working on hand independence. Very motivated, practicing consistently."
              />
              <Button variant="secondary" style={{ width: '100%', marginTop: '12px' }}>Save Notes</Button>
            </div>
          </section>
          
          <section className={styles.section}>
            <h2 className={styles.sectionTitle}>Upcoming Lessons</h2>
            <div className={styles.card}>
              <div className={styles.emptyState}>
                <Calendar size={32} color="var(--text-muted)" style={{ marginBottom: '12px' }} />
                <p>No upcoming scheduled lessons.</p>
              </div>
            </div>
          </section>
        </div>
      </div>
    </motion.div>
  );
}
