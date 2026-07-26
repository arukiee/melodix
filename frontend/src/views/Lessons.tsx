import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Filter, Plus, FileMusic, MoreVertical } from 'lucide-react';
import { motion } from 'framer-motion';
import { Button } from '../components/Button';
import { Input } from '../components/Input';
import styles from './Lessons.module.css';

const mockLessons = [
  { id: '1', title: 'Clair de Lune', composer: 'Claude Debussy', level: 'Intermediate', dateAdded: 'Oct 12, 2025' },
  { id: '2', title: 'Für Elise', composer: 'Ludwig van Beethoven', level: 'Beginner', dateAdded: 'Sep 28, 2025' },
  { id: '3', title: 'C Major Scale Exercise', composer: 'Teacher Created', level: 'Beginner', dateAdded: 'Yesterday' },
  { id: '4', title: 'Gymnopédie No.1', composer: 'Erik Satie', level: 'Intermediate', dateAdded: 'Oct 15, 2025' },
];

export function Lessons() {
  const navigate = useNavigate();
  const [search, setSearch] = useState('');

  const filteredLessons = mockLessons.filter(l => 
    l.title.toLowerCase().includes(search.toLowerCase()) || 
    l.composer.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <div>
          <h1 className={styles.title}>Lesson Library</h1>
          <p className={styles.subtitle}>Manage your sheet music, exercises, and MIDI files.</p>
        </div>
        <Button variant="primary" onClick={() => navigate('/teacher/lessons/upload')}>
          <Plus size={16} style={{ marginRight: '8px' }} />
          Upload Lesson
        </Button>
      </header>

      <div className={styles.toolbar}>
        <div className={styles.searchWrap}>
          <Input 
            label=""
            placeholder="Search lessons or composers..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <Button variant="secondary">
          <Filter size={16} style={{ marginRight: '8px' }} />
          Filter
        </Button>
      </div>

      <div className={styles.grid}>
        {filteredLessons.length === 0 ? (
          <div className={styles.emptyState}>
            <h3>No lessons found</h3>
            <p>Try adjusting your search or upload a new lesson.</p>
          </div>
        ) : (
          filteredLessons.map((lesson, index) => (
            <motion.div 
              key={lesson.id} 
              className={styles.card}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
            >
              <div className={styles.cardHeader}>
                <div className={styles.iconBox}>
                  <FileMusic size={24} color="var(--accent-primary)" />
                </div>
                <button className={styles.moreBtn} onClick={() => alert('Context menu')}>
                  <MoreVertical size={16} />
                </button>
              </div>
              <div className={styles.cardBody}>
                <h3 className={styles.lessonTitle}>{lesson.title}</h3>
                <p className={styles.lessonComposer}>{lesson.composer}</p>
                <div className={styles.cardMeta}>
                  <span className={styles.badge}>{lesson.level}</span>
                  <span className={styles.date}>{lesson.dateAdded}</span>
                </div>
              </div>
              <div className={styles.cardFooter}>
                <Button variant="secondary" style={{ width: '100%' }} onClick={() => navigate('/teacher/assignments/create')}>
                  Assign
                </Button>
              </div>
            </motion.div>
          ))
        )}
      </div>
    </div>
  );
}
