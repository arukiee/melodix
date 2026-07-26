import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Filter, Plus, Calendar, CheckCircle2, Clock } from 'lucide-react';
import { motion } from 'framer-motion';
import { Button } from '../components/Button';
import { Input } from '../components/Input';
import styles from './Assignments.module.css';

const mockAssignments = [
  { id: '1', title: 'C Major Scale Practice', target: 'Beginner Class', dueDate: 'Tomorrow', completed: 18, total: 24, status: 'active' },
  { id: '2', title: 'Moonlight Sonata - Measure 1-15', target: 'Sarah Jenkins', dueDate: 'In 3 days', completed: 0, total: 1, status: 'active' },
  { id: '3', title: 'Sight Reading Drill #4', target: 'Intermediate Class', dueDate: 'Past Due', completed: 6, total: 8, status: 'past_due' },
  { id: '4', title: 'Für Elise Full Run', target: 'Michael Chen', dueDate: 'Completed', completed: 1, total: 1, status: 'completed' },
];

export function Assignments() {
  const navigate = useNavigate();
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState<'all' | 'active' | 'completed'>('all');

  const filteredAssignments = mockAssignments.filter(a => {
    const matchesSearch = a.title.toLowerCase().includes(search.toLowerCase());
    if (filter === 'all') return matchesSearch;
    if (filter === 'active') return matchesSearch && (a.status === 'active' || a.status === 'past_due');
    return matchesSearch && a.status === 'completed';
  });

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
            placeholder="Search assignments..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div className={styles.filters}>
          <button className={`${styles.filterBtn} ${filter === 'all' ? styles.activeFilter : ''}`} onClick={() => setFilter('all')}>All</button>
          <button className={`${styles.filterBtn} ${filter === 'active' ? styles.activeFilter : ''}`} onClick={() => setFilter('active')}>Active</button>
          <button className={`${styles.filterBtn} ${filter === 'completed' ? styles.activeFilter : ''}`} onClick={() => setFilter('completed')}>Completed</button>
        </div>
      </div>

      <div className={styles.grid}>
        {filteredAssignments.length === 0 ? (
          <div className={styles.emptyState}>
            <h3>No assignments found</h3>
            <p>Try adjusting your filters or create a new assignment.</p>
          </div>
        ) : (
          filteredAssignments.map((assignment, index) => (
            <motion.div 
              key={assignment.id} 
              className={styles.card}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
            >
              <div className={styles.cardHeader}>
                <h3 className={styles.cardTitle}>{assignment.title}</h3>
                <span className={`${styles.statusBadge} ${styles[assignment.status]}`}>
                  {assignment.status === 'completed' ? <CheckCircle2 size={12} /> : <Clock size={12} />}
                  {assignment.status === 'past_due' ? 'Past Due' : assignment.status === 'completed' ? 'Completed' : 'Active'}
                </span>
              </div>
              <div className={styles.cardBody}>
                <div className={styles.metaRow}>
                  <span className={styles.metaLabel}>Assigned to:</span>
                  <span className={styles.metaValue}>{assignment.target}</span>
                </div>
                <div className={styles.metaRow}>
                  <span className={styles.metaLabel}>Due:</span>
                  <span className={`${styles.metaValue} ${assignment.status === 'past_due' ? styles.errorText : ''}`}>
                    {assignment.dueDate}
                  </span>
                </div>
                
                <div className={styles.progressSection}>
                  <div className={styles.progressHeader}>
                    <span className={styles.progressLabel}>Completion</span>
                    <span className={styles.progressRatio}>{assignment.completed}/{assignment.total}</span>
                  </div>
                  <div className={styles.progressBar}>
                    <div 
                      className={styles.progressFill} 
                      style={{ 
                        width: `${(assignment.completed / assignment.total) * 100}%`,
                        backgroundColor: assignment.completed === assignment.total ? 'var(--status-success)' : 'var(--accent-primary)'
                      }} 
                    />
                  </div>
                </div>
              </div>
              <div className={styles.cardFooter}>
                <Button variant="ghost" style={{ width: '100%' }}>View Details</Button>
              </div>
            </motion.div>
          ))
        )}
      </div>
    </div>
  );
}
