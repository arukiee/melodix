import { useNavigate, useParams, Link } from 'react-router-dom';
import { ArrowLeft, Sparkles, Heart } from 'lucide-react';
import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Button } from '../components/Button';
import { apiClient } from '../api/client';
import styles from './SongDetails.module.css';

interface SongDetailData {
  id: string;
  title: string;
  composer?: string;
  artist?: string;
  difficulty?: string;
  duration?: number;
  bpm?: number;
  thumbnail_url?: string;
  learning_objectives?: string[];
  ai_coaching_focus?: Record<string, any>;
}

export function SongDetails() {
  const navigate = useNavigate();
  const { songId } = useParams();
  const [song, setSong] = useState<SongDetailData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchSong = async () => {
      if (!songId) {
        setError('No song selected.');
        setIsLoading(false);
        return;
      }

      try {
        setIsLoading(true);
        const { data } = await apiClient.get(`/songs/${songId}`);
        setSong(data);
        setError(null);
      } catch (err: any) {
        console.error('Failed to load song details', err);
        setError('This song hasn’t been analyzed yet.');
      } finally {
        setIsLoading(false);
      }
    };

    fetchSong();
  }, [songId]);

  if (isLoading) {
    return (
      <motion.div className={styles.container} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}>
        <div style={{ color: 'var(--text-secondary)', padding: '32px 0' }}>Loading song details...</div>
      </motion.div>
    );
  }

  if (error || !song) {
    return (
      <motion.div className={styles.container} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}>
        <Link to="/library" className={styles.backLink}>
          <ArrowLeft size={20} /> Back to Library
        </Link>
        <div style={{ padding: '24px', color: 'var(--text-secondary)', background: 'var(--surface-color)', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
          {error || 'This song hasn’t been analyzed yet.'}
        </div>
      </motion.div>
    );
  }

  const songTitle = song.title;
  const composer = song.composer || song.artist || 'Unknown composer';
  const durationText = song.duration ? `${Math.floor(song.duration / 60)} minutes` : 'Unknown time';
  const bpmText = song.bpm ? `${song.bpm} BPM` : 'Tempo TBD';
  const artworkUrl = song.thumbnail_url || 'https://images.unsplash.com/photo-1520523839897-bd0b52f945a0?q=80&w=300&auto=format&fit=crop';
  const skills = song.learning_objectives && song.learning_objectives.length > 0 ? song.learning_objectives : ['Technique', 'Rhythm', 'Expression'];
  const aiPrediction = song.ai_coaching_focus && Object.keys(song.ai_coaching_focus).length > 0
    ? JSON.stringify(song.ai_coaching_focus)
    : `Perfect for your current skill level. Focus on expression and control in ${songTitle}.`;

  const handleStartPractice = () => {
    if (!songId) return;
    navigate(`/studio/${songId}`);
  };

  return (
    <motion.div 
      className={styles.container}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <Link to="/library" className={styles.backLink}>
        <ArrowLeft size={20} /> Back to Library
      </Link>

      <div className={styles.hero}>
        <img src={artworkUrl} alt={songTitle} className={styles.artwork} />
        
        <div className={styles.info}>
          <h1 className={styles.title}>{songTitle}</h1>
          <p className={styles.composer}>{composer}</p>
          
          <div className={styles.actions}>
            <Button 
              variant="primary" 
              onClick={handleStartPractice}
            >
              Start Practice
            </Button>
            <button className={styles.favoriteBtn} aria-label="Add to favorites">
              <Heart size={20} />
            </button>
          </div>

          <div className={styles.metadataGrid}>
            <div className={styles.metaItem}>
              <span className={styles.metaLabel}>Difficulty</span>
              <span className={styles.metaValue}>{song.difficulty || 'Beginner'}</span>
            </div>
            <div className={styles.metaItem}>
              <span className={styles.metaLabel}>Est. Time</span>
              <span className={styles.metaValue}>{durationText}</span>
            </div>
            <div className={styles.metaItem}>
              <span className={styles.metaLabel}>Tempo</span>
              <span className={styles.metaValue}>{bpmText}</span>
            </div>
          </div>
        </div>
      </div>

      <div className={styles.aiPrediction}>
        <Sparkles size={24} className={styles.aiIcon} />
        <div>
          <h3 className={styles.aiTitle}>AI Recommendation</h3>
          <p className={styles.aiText}>{aiPrediction}</p>
        </div>
      </div>

      <div className={styles.skillsSection}>
        <h3 className={styles.skillsTitle}>Skills Required</h3>
        <div className={styles.skillsList}>
          {skills.map(skill => (
            <div key={skill} className={styles.skillBadge}>{skill}</div>
          ))}
        </div>
      </div>
    </motion.div>
  );
}
