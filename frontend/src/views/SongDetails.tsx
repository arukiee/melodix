
import { useNavigate, useParams, Link } from 'react-router-dom';
import { ArrowLeft, Sparkles, Heart } from 'lucide-react';
import { motion } from 'framer-motion';
import { Button } from '../components/Button';
import styles from './SongDetails.module.css';

export function SongDetails() {
  const navigate = useNavigate();
  const { songId } = useParams();

  // Mock data for the specific song
  const song = {
    title: 'Moonlight Sonata (1st Movement)',
    composer: 'Ludwig van Beethoven',
    difficulty: 'Intermediate',
    duration: '14 minutes',
    bpm: '60 BPM',
    artworkUrl: 'https://images.unsplash.com/photo-1520523839897-bd0b52f945a0?q=80&w=300&auto=format&fit=crop',
    skills: ['Arpeggios', 'Dynamics', 'Hand Coordination', 'Pedaling'],
    aiPrediction: 'Perfect for your current skill level. Focus on keeping the triplet accompaniment extremely soft while letting the top melody line sing.'
  };

  return (
    <motion.div 
      className={styles.container}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <Link to="/learn" className={styles.backLink}>
        <ArrowLeft size={20} /> Back to Discover
      </Link>

      <div className={styles.hero}>
        <img src={song.artworkUrl} alt={song.title} className={styles.artwork} />
        
        <div className={styles.info}>
          <h1 className={styles.title}>{song.title}</h1>
          <p className={styles.composer}>{song.composer}</p>
          
          <div className={styles.actions}>
            <Button 
              variant="primary" 
              onClick={() => navigate(`/studio/${songId}`)}
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
              <span className={styles.metaValue}>{song.difficulty}</span>
            </div>
            <div className={styles.metaItem}>
              <span className={styles.metaLabel}>Est. Time</span>
              <span className={styles.metaValue}>{song.duration}</span>
            </div>
            <div className={styles.metaItem}>
              <span className={styles.metaLabel}>Tempo</span>
              <span className={styles.metaValue}>{song.bpm}</span>
            </div>
          </div>
        </div>
      </div>

      <div className={styles.aiPrediction}>
        <Sparkles size={24} className={styles.aiIcon} />
        <div>
          <h3 className={styles.aiTitle}>AI Recommendation</h3>
          <p className={styles.aiText}>{song.aiPrediction}</p>
        </div>
      </div>

      <div className={styles.skillsSection}>
        <h3 className={styles.skillsTitle}>Skills Required</h3>
        <div className={styles.skillsList}>
          {song.skills.map(skill => (
            <div key={skill} className={styles.skillBadge}>{skill}</div>
          ))}
        </div>
      </div>
    </motion.div>
  );
}
