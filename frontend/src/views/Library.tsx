import { useState } from 'react';
import { Search, ArrowLeft, Clock, Calendar } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/Button';
import styles from './Library.module.css';

const mockLibrary = [
  { 
    id: '1', title: 'Clair de Lune', composer: 'Claude Debussy', difficulty: 'Advanced', 
    duration: '15 min', progress: 85, lastPracticed: 'Yesterday', category: 'continue', type: 'built-in' 
  },
  { 
    id: '2', title: 'Minuet in G Major', composer: 'J.S. Bach', difficulty: 'Beginner', 
    duration: '5 min', progress: 100, lastPracticed: '1 week ago', category: 'favorites', type: 'built-in' 
  },
  { 
    id: '3', title: 'Nocturne Op. 9 No. 2', composer: 'Frédéric Chopin', difficulty: 'Intermediate', 
    duration: '12 min', progress: 30, lastPracticed: '2 days ago', category: 'continue', type: 'built-in' 
  },
  { 
    id: '4', title: 'Hanon Exercise No. 1', composer: 'Charles-Louis Hanon', difficulty: 'Beginner', 
    duration: '10 min', progress: 0, lastPracticed: 'Never', category: 'exercises', type: 'built-in' 
  },
  { 
    id: '5', title: 'My Custom Arrangement', composer: 'Me', difficulty: 'Intermediate', 
    duration: '4 min', progress: 10, lastPracticed: '3 days ago', category: 'uploads', type: 'ai-generated' 
  },
];

export function Library() {
  const navigate = useNavigate();
  const [filter, setFilter] = useState('All');

  const continueLearning = mockLibrary.filter(s => s.category === 'continue' || (s.progress > 0 && s.progress < 100));
  const myUploads = mockLibrary.filter(s => s.category === 'uploads');
  const teacherAssignments = mockLibrary.filter(s => s.category === 'assignments'); // Empty for demo
  const favorites = mockLibrary.filter(s => s.category === 'favorites');
  const exercises = mockLibrary.filter(s => s.category === 'exercises');

  const renderSection = (title: string, songs: typeof mockLibrary) => {
    if (songs.length === 0) return null;
    return (
      <div className={styles.categorySection}>
        <h2 className={styles.categoryTitle}>{title}</h2>
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
                  <p className={styles.composer}>{song.composer}</p>
                </div>
                <span className={styles.badge}>{song.difficulty}</span>
              </div>
              
              <div className={styles.cardMeta}>
                <div className={styles.metaItem}>
                  <Clock size={14} />
                  <span>{song.duration}</span>
                </div>
                <div className={styles.metaItem}>
                  <Calendar size={14} />
                  <span>{song.lastPracticed}</span>
                </div>
                <div className={styles.metaItem}>
                  <span className={styles.badge}>{song.type === 'ai-generated' ? 'AI Generated' : 'Built-in'}</span>
                </div>
              </div>

              <div className={styles.progressContainer}>
                <div className={styles.progressBar}>
                  <div className={styles.progressFill} style={{ width: `${song.progress}%` }} />
                </div>
                <div className={styles.progressLabel}>
                  <span>{song.progress > 0 ? 'Continue Practice' : 'Start Practice'}</span>
                  <span>{song.progress}%</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
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
          <div className={styles.searchWrapper}>
            <Search size={20} className={styles.searchIcon} />
            <input 
              type="text" 
              className={styles.searchInput} 
              placeholder="Search by title, composer, or genre..."
            />
          </div>
          <div className={styles.filters}>
            <Button variant={filter === 'All' ? 'secondary' : 'ghost'} onClick={() => setFilter('All')} style={{ padding: '8px 16px', fontSize: '14px' }}>All</Button>
            <Button variant={filter === 'Favorites' ? 'secondary' : 'ghost'} onClick={() => setFilter('Favorites')} style={{ padding: '8px 16px', fontSize: '14px' }}>Favorites</Button>
            <Button variant={filter === 'My Uploads' ? 'secondary' : 'ghost'} onClick={() => setFilter('My Uploads')} style={{ padding: '8px 16px', fontSize: '14px' }}>My Uploads</Button>
            <Button variant={filter === 'Exercises' ? 'secondary' : 'ghost'} onClick={() => setFilter('Exercises')} style={{ padding: '8px 16px', fontSize: '14px' }}>Exercises</Button>
          </div>
        </div>
      </header>

      {mockLibrary.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '64px 0', color: 'var(--text-secondary)' }}>
          <p>No songs yet. Upload your first song or explore the built-in library.</p>
        </div>
      ) : (
        <>
          {renderSection('Continue Learning', continueLearning)}
          {renderSection('My Uploads', myUploads)}
          {renderSection('Teacher Assignments', teacherAssignments)}
          {renderSection('Favorites', favorites)}
          {renderSection('Exercises', exercises)}
        </>
      )}
    </div>
  );
}
