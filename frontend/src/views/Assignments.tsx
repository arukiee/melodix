import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, CheckCircle2, Clock, Loader2 } from 'lucide-react';
import { motion } from 'framer-motion';
import { Button } from '../components/Button';
import { Input } from '../components/Input';
import { apiClient } from '../api/client';
import styles from './Assignments.module.css';

interface AssignmentItem {
  id: string;
  title: string;
  description?: string;
  category?: string;
  difficulty?: string;
  estimated_duration?: number;
  teacher?: {
    full_name: string;
  };
  created_at: string;
}

export function Assignments() {
  const navigate = useNavigate();
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState<'all' | 'active' | 'completed'>('all');
  const [assignments, setAssignments] = useState<AssignmentItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const fetchAssignments = async () => {
    setIsLoading(true);
    try {
      const { data } = await apiClient.get('/lessons');
      setAssignments(data.items || []);
    } catch (err) {
      console.error('Failed to fetch assignments:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchAssignments();
  }, []);

  const filteredAssignments = assignments.filter(a =>
    a.title.toLowerCase().includes(search.toLowerCase()) ||
    (a.description || '').toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <div>
          <h1 className={styles.title}>Assignments</h1>
          <p className={styles.subtitle}>Track practice tasks for your students and classes.</p>
        </div>
        <Button variant="primary" onClick={() => navigate('/teacher/assignments/create')}>
          <Plus size={16} style={{ marginRight: '8px' }} />
          Create Assignment
        </Button>
      </header>

      <div className={styles.toolbar}>
        <div className={styles.searchWrap}>
          <Input 
            label=""
            placeholder="Search assignments by title or description..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div className={styles.filters}>
          <button className={`${styles.filterBtn} ${filter === 'all' ? styles.active : ''}`} onClick={() => setFilter('all')}>All</button>
          <button className={`${styles.filterBtn} ${filter === 'active' ? styles.active : ''}`} onClick={() => setFilter('active')}>Active</button>
          <button className={`${styles.filterBtn} ${filter === 'completed' ? styles.active : ''}`} onClick={() => setFilter('completed')}>Completed</button>
        </div>
      </div>

      {isLoading ? (
        <div style={{ textAlign: 'center', padding: '64px 0' }}>
          <Loader2 size={36} className="spin" color="var(--accent-primary)" />
          <p style={{ marginTop: '12px', color: 'var(--text-secondary)' }}>Loading assignments...</p>
        </div>
      ) : filteredAssignments.length === 0 ? (
        <div className={styles.emptyState}>
          <Clock size={48} color="var(--text-muted)" style={{ marginBottom: '16px' }} />
          <h3>No assignments found</h3>
          <p>Create your first assignment using the button above.</p>
        </div>
      ) : (
        <div className={styles.grid}>
          {filteredAssignments.map((a) => (
            <motion.div 
              key={a.id} 
              className={styles.card}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
            >
              <div className={styles.cardHeader}>
                <div>
                  <h3 className={styles.assignmentTitle}>{a.title}</h3>
                  <div className={styles.target}>{a.description || 'Practice assignment'}</div>
                </div>
                <span className={`${styles.statusBadge} ${styles.active}`}>
                  Active
                </span>
              </div>

              <div className={styles.metaRow}>
                <div className={styles.metaItem}>
                  <Clock size={14} />
                  <span>{a.estimated_duration || 20} mins</span>
                </div>
                <div className={styles.metaItem}>
                  <CheckCircle2 size={14} />
                  <span>Teacher: {a.teacher?.full_name || 'Instructor'}</span>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}
