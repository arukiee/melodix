import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Play } from 'lucide-react';
import { Button } from '../components/Button';
import { PracticeAnalytics } from '../components/Learn/PracticeAnalytics';
import { xpService } from '../services/xpService';
import styles from './Progress.module.css';

export function Progress() {
  const navigate = useNavigate();
  const totalXP = xpService.getTotalXP();
  const level = xpService.getLevel();
  const levelTitle = xpService.getLevelTitle();
  const streak = xpService.getStreak();
  const { current: levelXP, needed: levelNeeded } = xpService.getProgressToNextLevel();
  const hasData = xpService.getRecentSessions(1).length > 0;

  return (
    <motion.div
      className={styles.container}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <header className={styles.header} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', flexWrap: 'wrap', gap: '16px', marginBottom: '32px' }}>
        <div>
          <h1 className={styles.title}>Progress</h1>
          <p className={styles.subtitle}>Your learning journey at a glance</p>
        </div>

        {/* Hero level pill */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '16px',
          padding: '12px 20px',
          background: 'var(--bg-card)',
          border: '1px solid var(--border-color)',
          borderRadius: '16px',
        }}>
          <div>
            <div style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Your Level</div>
            <div style={{ fontSize: '1.1rem', fontWeight: 800 }}>Level {level} — {levelTitle}</div>
          </div>
          <div style={{ height: '36px', width: '1px', background: 'var(--border-color)' }} />
          <div>
            <div style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>XP Total</div>
            <div style={{ fontSize: '1.1rem', fontWeight: 800, color: '#f59e0b' }}>{totalXP.toLocaleString()}</div>
          </div>
          <div style={{ height: '36px', width: '1px', background: 'var(--border-color)' }} />
          <div>
            <div style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Streak</div>
            <div style={{ fontSize: '1.1rem', fontWeight: 800, color: '#ef4444' }}>🔥 {streak} days</div>
          </div>
        </div>
      </header>

      {/* Level progress bar */}
      {hasData && (
        <div style={{ marginBottom: '28px', padding: '16px 20px', background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px', fontSize: '0.82rem' }}>
            <span style={{ color: 'var(--text-secondary)' }}>Progress to Level {level + 1}</span>
            <span style={{ color: 'var(--text-muted)' }}>{levelXP} / {levelNeeded} XP</span>
          </div>
          <div style={{ height: '8px', background: 'var(--bg-elevated)', borderRadius: '4px', overflow: 'hidden' }}>
            <div style={{
              height: '100%',
              width: `${Math.min(100, Math.round((levelXP / levelNeeded) * 100))}%`,
              background: 'linear-gradient(90deg, #8b5cf6, #3b82f6)',
              borderRadius: '4px',
              transition: 'width 0.6s ease',
            }} />
          </div>
        </div>
      )}

      <PracticeAnalytics />

      {!hasData && (
        <div style={{ textAlign: 'center', marginTop: '32px' }}>
          <Button variant="primary" onClick={() => navigate('/learn')} style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}>
            <Play size={16} /> Start Piano Journey
          </Button>
        </div>
      )}
    </motion.div>
  );
}
