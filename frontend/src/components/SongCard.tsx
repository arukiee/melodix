import { Play, Music, Globe, Database, ExternalLink } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import styles from './SongCard.module.css';

export interface SongCardProps {
  id: string;
  title: string;
  composer: string;
  difficulty?: string;
  duration?: string;
  progress?: number;
  artworkUrl?: string;
  source?: 'Local' | 'MIDI Repo' | 'MuseScore' | 'IMSLP' | 'Ultimate Guitar' | 'YouTube' | string;
  loading?: boolean;
}

export function SongCard({ id, title, composer, difficulty, duration, progress, artworkUrl, source, loading }: SongCardProps) {
  const navigate = useNavigate();

  if (loading) {
    return (
      <div className={`${styles.songCard} ${styles.loadingState}`}>
        <div className={styles.loadingSpinner} />
      </div>
    );
  }

  const getSourceIcon = () => {
    switch(source) {
      case 'YouTube': return <Globe size={14} />;
      case 'Local': return <Database size={14} />;
      default: return <ExternalLink size={14} />;
    }
  };

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
        {source && (
          <div className={styles.sourceBadge}>
            {getSourceIcon()} {source}
          </div>
        )}
      </div>
      <div className={styles.info}>
        <h3 className={styles.title}>{title}</h3>
        <p className={styles.composer}>{composer}</p>
        <div className={styles.meta}>
          {difficulty && <span className={styles.difficulty}>{difficulty}</span>}
          {difficulty && duration && <span className={styles.dot}>•</span>}
          {duration && <span className={styles.duration}>{duration}</span>}
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
