import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Filter, Plus, FileMusic, Trash2, Edit2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '../components/Button';
import { Input } from '../components/Input';
import { lessonsApi } from '../api/lessons';
import type { Lesson } from '../api/lessons';
import styles from './Lessons.module.css';

export function Lessons() {
  const navigate = useNavigate();
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const fetchLessons = async () => {
    try {
      setLoading(true);
      const data = await lessonsApi.getTeacherLessons();
      setLessons(data.items);
    } catch (err) {
      console.error('Failed to load teacher lessons', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLessons();
  }, []);

  const filteredLessons = lessons.filter(l => 
    l.title.toLowerCase().includes(search.toLowerCase()) || 
    (l.genre && l.genre.toLowerCase().includes(search.toLowerCase())) ||
    (l.category && l.category.toLowerCase().includes(search.toLowerCase()))
  );

  const handleDelete = async (id: string) => {
    if (!window.confirm("Are you sure you want to delete this lesson?")) return;
    
    try {
      setDeletingId(id);
      await lessonsApi.deleteLesson(id);
      setLessons(prev => prev.filter(l => l.id !== id));
    } catch (err) {
      console.error('Failed to delete lesson', err);
      alert('Failed to delete lesson.');
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <div>
          <h1 className={styles.title}>Lesson Library</h1>
          <p className={styles.subtitle}>Manage your sheet music, exercises, and MIDI files.</p>
        </div>
        <Button variant="primary" onClick={() => navigate('/teacher/lessons/upload')}>
          <Plus size={16} style={{ marginRight: '8px' }} />
          Create Lesson
        </Button>
      </header>

      <div className={styles.toolbar}>
        <div className={styles.searchWrap}>
          <Search size={18} className={styles.searchIcon} />
          <Input 
            label=""
            placeholder="Search lessons or categories..."
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
        {loading ? (
          <div className={styles.loading}>Loading lessons...</div>
        ) : filteredLessons.length === 0 ? (
          <div className={styles.emptyState}>
            <h3>No lessons found</h3>
            <p>Try adjusting your search or upload a new lesson.</p>
          </div>
        ) : (
          <AnimatePresence>
            {filteredLessons.map((lesson, index) => (
              <motion.div 
                key={lesson.id} 
                className={styles.card}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95 }}
                transition={{ delay: index * 0.05 }}
              >
                <div className={styles.cardHeader}>
                  <div className={styles.iconBox}>
                    <FileMusic size={24} color="var(--accent-primary)" />
                  </div>
                  <div className={styles.actions}>
                    <button 
                      className={styles.iconBtn} 
                      onClick={() => navigate(`/teacher/lessons/edit/${lesson.id}`)}
                      title="Edit Lesson"
                    >
                      <Edit2 size={16} />
                    </button>
                    <button 
                      className={`${styles.iconBtn} ${styles.danger}`} 
                      onClick={() => handleDelete(lesson.id)}
                      disabled={deletingId === lesson.id}
                      title="Delete Lesson"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                </div>
                <div className={styles.cardBody}>
                  <h3 className={styles.lessonTitle}>
                    {lesson.title}
                    {!lesson.is_published && <span className={styles.draftBadge}>Draft</span>}
                  </h3>
                  <p className={styles.lessonComposer}>{lesson.category || 'Uncategorized'}</p>
                  <div className={styles.cardMeta}>
                    <span className={styles.badge}>
                      {lesson.difficulty ? lesson.difficulty.charAt(0) + lesson.difficulty.slice(1).toLowerCase() : 'Beginner'}
                    </span>
                    <span className={styles.date}>
                      {new Date(lesson.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
                <div className={styles.cardFooter}>
                  <Button variant="secondary" style={{ width: '100%' }} onClick={() => navigate('/teacher/assignments/create')}>
                    Assign
                  </Button>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        )}
      </div>
    </div>
  );
}
