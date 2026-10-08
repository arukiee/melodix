import { useState, useEffect } from 'react';
import { ArrowLeft, Clock, Music, Loader2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/Button';
import { apiClient } from '../api/client';
import { UniversalSearch } from '../components/Library/UniversalSearch';
import styles from './Library.module.css';

interface SongItem {
  id: string;
  title: string;
  composer?: string;
  artist?: string;
  genre?: string;
  difficulty?: string;
  bpm?: number;
  duration?: number; // in seconds
  file_url?: string;
  thumbnail_url?: string;
}

export function Library() {
  const navigate = useNavigate();
  const [filter, setFilter] = useState('All');
  const [searchQuery] = useState('');
  const [songs, setSongs] = useState<SongItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const fetchSongs = async (query = '', difficultyFilter = 'All') => {
    setIsLoading(true);
    try {
      const params: Record<string, string> = {};
      if (query.trim()) params.q = query.trim();
      if (difficultyFilter !== 'All' && difficultyFilter !== 'My Uploads' && difficultyFilter !== 'Favorites') {
        params.difficulty = difficultyFilter;
      }
      const { data } = await apiClient.get('/songs', { params });
      setSongs(data);
    } catch (err) {
      console.error('Failed to fetch songs:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchSongs('', filter);
  }, [filter]);

  const formatDuration = (seconds?: number) => {
    if (!seconds) return '3 min';
    const mins = Math.floor(seconds / 60);
    return `${mins} min`;
  };

  return (
    <div className={styles.library}>
      <header className={styles.header}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '24px' }}>
          <button onClick={() => navigate('/dashboard')} style={{ background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', display: 'flex' }}>
            <ArrowLeft size={24} />
          </button>
          <h1 className={styles.title} style={{ marginBottom: 0 }}>Library</h1>
        </div>
        <div className={styles.actionBar}>
          <div className={styles.searchWrapper} style={{ width: '100%', maxWidth: '600px', margin: '0 auto' }}>
            <UniversalSearch />
          </div>
          <div className={styles.filters}>
            {['All', 'Beginner', 'Intermediate', 'Advanced'].map((diff) => (
              <Button 
                key={diff}
                variant={filter === diff ? 'secondary' : 'ghost'} 
                onClick={() => setFilter(diff)} 
                style={{ padding: '8px 16px', fontSize: '14px' }}
              >
                {diff}
              </Button>
            ))}
          </div>
        </div>
      </header>

      {isLoading ? (
        <div style={{ textAlign: 'center', padding: '64px 0' }}>
          <Loader2 size={36} className="spin" color="var(--accent-primary)" />
          <p style={{ marginTop: '16px', color: 'var(--text-secondary)' }}>Loading catalog pieces...</p>
        </div>
      ) : songs.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '64px 0', color: 'var(--text-secondary)' }}>
          <Music size={48} color="var(--text-muted)" style={{ marginBottom: '16px' }} />
          <h3>{searchQuery ? 'No songs found' : 'Your library is empty'}</h3>
          <p>{searchQuery ? `No catalog pieces matched "${searchQuery}".` : 'Import your first song.'}</p>
        </div>
      ) : (
        <div className={styles.categorySection}>
          <h2 className={styles.categoryTitle}>Catalog Pieces ({songs.length})</h2>
          <div className={styles.grid}>
            {songs.map((song) => (
              <div 
                key={song.id} 
                className={styles.songCard} 
                onClick={() => navigate(`/song/${song.id}`)}
              >
                <div className={styles.cardHeader}>
                  <div>
                    <h3 className={styles.songTitle}>{song.title}</h3>
                    <p className={styles.composer}>{song.composer || song.artist || 'Classical'}</p>
                  </div>
                  <span className={styles.badge}>{song.difficulty || 'Beginner'}</span>
                </div>
                
                <div className={styles.cardMeta}>
                  <div className={styles.metaItem}>
                    <Clock size={14} />
                    <span>{formatDuration(song.duration)}</span>
                  </div>
                  <div className={styles.metaItem}>
                    <span className={styles.badge}>{song.genre || 'Piano'}</span>
                  </div>
                </div>

                <div className={styles.progressContainer}>
                  <div className={styles.progressBar}>
                    <div className={styles.progressFill} style={{ width: '0%' }} />
                  </div>
                  <div className={styles.progressLabel}>
                    <span>Start Practice</span>
                    <span>Ready</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
