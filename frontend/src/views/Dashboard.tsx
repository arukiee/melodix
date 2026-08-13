import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Flame, Sparkles, BookOpen, Clock, Target, PlayCircle, Loader2 } from 'lucide-react';
import { Button } from '../components/Button';
import { motion } from 'framer-motion';
import { useUser } from '../context/UserContext';
import { apiClient } from '../api/client';
import styles from './Dashboard.module.css';

interface CurriculumLesson {
  id: string;
  title: string;
  slug: string;
  description: string;
  category: string;
  difficulty: string;
  genre: string;
  estimated_duration: number;
  display_order: number;
  objectives: Array<{ id: string; title: string; description: string }>;
}

export function Dashboard() {
  const navigate = useNavigate();
  const { profile } = useUser();
  const userName = profile.firstName || profile.full_name?.split(' ')[0] || profile.email?.split('@')[0] || 'Musician';
  const [curriculum, setCurriculum] = useState<CurriculumLesson[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchCurriculum = async () => {
      setIsLoading(true);
      try {
        const { data } = await apiClient.get('/lessons', { params: { page_size: 20 } });
        setCurriculum(data.items || []);
      } catch (err) {
        console.error('Failed to fetch curriculum lessons:', err);
      } finally {
        setIsLoading(false);
      }
    };
    fetchCurriculum();
  }, []);

  const activeLesson = curriculum.length > 0 ? curriculum[0] : null;

  return (
    <motion.div 
      className={styles.dashboard}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <header className={styles.header}>
        <h1 className={styles.greeting}>Good Afternoon, {userName}</h1>
        <div className={styles.date}>Personalized AI Piano Curriculum</div>
      </header>

      {/* Main Learning Hero */}
      <div className={styles.grid}>
        <div className={styles.continueSection}>
          <div className={styles.card} style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            <h2 className={styles.cardTitle}>Up Next in Curriculum</h2>
            {isLoading ? (
              <div style={{ textAlign: 'center', padding: '48px 0' }}>
                <Loader2 size={36} className="spin" color="var(--accent-primary)" />
                <p style={{ marginTop: '12px', color: 'var(--text-secondary)' }}>Loading your curriculum path...</p>
              </div>
            ) : activeLesson ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', flex: 1, padding: '16px 0' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div>
                    <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--accent-primary)', textTransform: 'uppercase' }}>
                      Lesson #{activeLesson.display_order} • {activeLesson.category}
                    </span>
                    <h3 style={{ fontSize: '22px', marginTop: '4px', fontWeight: 600 }}>{activeLesson.title}</h3>
                  </div>
                  <span className={styles.badge} style={{ padding: '4px 10px', borderRadius: '12px', background: 'rgba(59, 130, 246, 0.1)', color: 'var(--accent-primary)', fontSize: '12px', fontWeight: 600 }}>
                    {activeLesson.difficulty}
                  </span>
                </div>

                <p style={{ color: 'var(--text-secondary)', fontSize: '14px', lineHeight: 1.5 }}>
                  {activeLesson.description}
                </p>

                <div style={{ display: 'flex', gap: '16px', fontSize: '13px', color: 'var(--text-muted)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Clock size={16} />
                    <span>{activeLesson.estimated_duration} mins</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Target size={16} />
                    <span>{activeLesson.objectives?.length || 2} Objectives</span>
                  </div>
                </div>

                <div style={{ marginTop: 'auto', paddingTop: '16px' }}>
                  <Button 
                    variant="primary" 
                    onClick={() => navigate('/learn')}
                    style={{ width: '100%', display: 'flex', justifyContent: 'center', gap: '8px' }}
                  >
                    <PlayCircle size={18} /> Start Piano Journey
                  </Button>
                </div>
              </div>
            ) : (
              <div style={{ textAlign: 'center', padding: '32px 0', color: 'var(--text-secondary)' }}>
                <BookOpen size={48} color="var(--text-muted)" style={{ margin: '0 auto 16px' }} />
                <p>No lesson selected.<br/>Choose a song to start practicing.</p>
              </div>
            )}
          </div>
        </div>

        {/* Right Stats & AI Panel */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <div className={`${styles.card} ${styles.goalCard}`}>
            <h2 className={styles.cardTitle} style={{ justifyContent: 'center' }}>Daily Goal</h2>
            <div className={styles.goalCircle}>
              <svg width="120" height="120" viewBox="0 0 120 120">
                <circle cx="60" cy="60" r="54" fill="none" stroke="var(--bg-elevated)" strokeWidth="8" />
                <circle cx="60" cy="60" r="54" fill="none" stroke="var(--accent-primary)" strokeWidth="8" strokeDasharray="339" strokeDashoffset="180" strokeLinecap="round" style={{ transform: 'rotate(-90deg)', transformOrigin: '50% 50%' }} />
              </svg>
              <div className={styles.goalText}>15<span style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>/30</span></div>
            </div>
            <div className={styles.goalLabel}>minutes practice completed</div>
          </div>

          <div className={`${styles.card} ${styles.aiPanel}`}>
            <h2 className={styles.cardTitle} style={{ color: 'var(--semantic-ai)' }}>
              <Sparkles size={20} /> AI Curriculum Coach
            </h2>
            <p className={styles.aiText}>
              Start practicing to let AI curriculum coach guide you.
            </p>
          </div>
        </div>
      </div>

      {/* 3-Tier Curriculum Path Section */}
      <section className={styles.section} style={{ marginTop: '48px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
          <h2 className={styles.cardTitle} style={{ marginBottom: 0 }}>
            <BookOpen size={20} color="var(--accent-primary)" style={{ marginRight: '8px' }} />
            Structured Curriculum Progression ({curriculum.length} Lessons)
          </h2>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--status-warning)', fontWeight: 600 }}>
            <Flame size={20} /> Active Learner
          </div>
        </div>

        {curriculum.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '48px 0', background: 'var(--surface-color)', borderRadius: 'var(--radius-card)' }}>
            <p style={{ color: 'var(--text-secondary)' }}>No lessons available. Please import a song first.</p>
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '20px' }}>
            {curriculum.map((lesson) => (
              <div 
                key={lesson.id}
                className={styles.card}
                onClick={() => navigate('/learn')}
                style={{ cursor: 'pointer', transition: 'transform 0.2s ease', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}
              >
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                    <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--accent-primary)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                      Lesson #{lesson.display_order} • {lesson.category}
                    </span>
                    <span style={{ fontSize: '11px', fontWeight: 600, padding: '2px 8px', borderRadius: '10px', background: 'var(--bg-elevated)', color: 'var(--text-secondary)' }}>
                      {lesson.difficulty}
                    </span>
                  </div>

                  <h3 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '8px' }}>{lesson.title}</h3>
                  <p style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: 1.4, marginBottom: '16px' }}>
                    {lesson.description}
                  </p>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '12px', borderTop: '1px solid var(--border-color)', fontSize: '12px', color: 'var(--text-muted)' }}>
                  <span>{lesson.estimated_duration} mins duration</span>
                  <span style={{ color: 'var(--accent-primary)', fontWeight: 600 }}>Start Lesson →</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </motion.div>
  );
}
