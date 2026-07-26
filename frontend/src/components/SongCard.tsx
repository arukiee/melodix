
import { Play, Music } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import styles from './SongCard.module.css';

export interface SongCardProps {
  id: string;
  title: string;
  composer: string;
  difficulty: string;
  duration: string;
  progress?: number;
  artworkUrl?: string;
}

export function SongCard({ id, title, composer, difficulty, duration, progress, artworkUrl }: SongCardProps) {
  const navigate = useNavigate();

  return (
    <div className={styles.songCard} onClick={() => navigate(`/song/${id}`)}>
      <div className={styles.artworkContainer}>
        {artworkUrl ? (
          <img src={artworkUrl} alt={title} className={styles.artwork} />
        ) : (
          <div style={{ width: '100%', height: '100%', background: 'linear-gradient(135deg, #121212, #1C1C1C)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Music size={40} color="var(--text-muted)" />
          </div>
        )}
        <div className={styles.playOverlay}>
          <div className={styles.playButton}>
            <Play size={24} fill="currentColor" />
          </div>
        </div>
      </div>
      <div className={styles.info}>
        <h3 className={styles.title}>{title}</h3>
        <p className={styles.composer}>{composer}</p>
        <div className={styles.meta}>
          <span className={styles.difficulty}>{difficulty}</span>
          <span className={styles.dot}>•</span>
          <span className={styles.duration}>{duration}</span>
        </div>
        
        {progress !== undefined && (
          <div className={styles.progressContainer}>
            <div className={styles.progressBar}>
              <div className={styles.progressFill} style={{ width: `${progress}%` }}></div>
            </div>
            {progress > 0 && <span className={styles.progressText}>{progress}%</span>}
          </div>
        )}
      </div>
    </div>
  );
}
