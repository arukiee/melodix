import { ArrowLeft, Settings, Volume2, Maximize, Minimize } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import styles from './StudioTopBar.module.css';

interface StudioTopBarProps {
  isFocusMode: boolean;
  toggleFocusMode: () => void;
}

export function StudioTopBar({ isFocusMode, toggleFocusMode }: StudioTopBarProps) {
  const navigate = useNavigate();

  if (isFocusMode) {
    return (
      <div className={styles.focusModeToggleBtn} onClick={toggleFocusMode}>
        <Minimize size={16} style={{ marginRight: '8px' }} />
        Exit Focus
      </div>
    );
  }

  return (
    <header className={styles.topBar}>
      <div className={styles.headerLeft}>
        <button className={styles.iconBtn} onClick={() => navigate('/dashboard')} aria-label="Back">
          <ArrowLeft size={24} />
        </button>
        <div>
          <div className={styles.songTitle}>Clair de Lune</div>
          <div className={styles.composer}>Claude Debussy • Intermediate</div>
        </div>
      </div>

      <div className={styles.headerStats}>
        <div className={styles.statGroup}>
          <span className={styles.statLabel}>Timer</span>
          <span className={styles.statValue}>12:45</span>
        </div>
        <div className={styles.statGroup}>
          <span className={styles.statLabel}>BPM</span>
          <span className={styles.statValue}>72</span>
        </div>
        <div className={styles.statGroup}>
          <span className={styles.statLabel}>Current Tempo</span>
          <span className={styles.statValue}>100%</span>
        </div>
        <div className={styles.statGroup}>
          <span className={styles.statLabel}>Score</span>
          <span className={styles.statValue}>12,450</span>
        </div>
      </div>

      <div className={styles.controls}>
        <button className={styles.iconBtn} aria-label="Volume">
          <Volume2 size={24} />
        </button>
        <button className={styles.iconBtn} aria-label="Settings">
          <Settings size={24} />
        </button>
        <button className={styles.iconBtn} onClick={toggleFocusMode} aria-label="Full Screen">
          <Maximize size={24} />
        </button>
      </div>
    </header>
  );
}
