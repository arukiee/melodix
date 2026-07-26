import { useNavigate } from 'react-router-dom';
import { Plus, Search, Filter, MoreHorizontal, Layers } from 'lucide-react';
import { motion } from 'framer-motion';
import { Button } from '../components/Button';
import styles from './Classes.module.css';

const mockClasses = [
  { id: '1', name: 'Beginner Piano', students: 12, avgAccuracy: '88%', avgPractice: '3.2 hrs/wk', pendingAssignments: 2, status: 'Active' },
  { id: '2', name: 'Intermediate Piano', students: 8, avgAccuracy: '92%', avgPractice: '5.1 hrs/wk', pendingAssignments: 4, status: 'Active' },
  { id: '3', name: 'Grade 1 Theory & Prep', students: 15, avgAccuracy: '85%', avgPractice: '2.5 hrs/wk', pendingAssignments: 1, status: 'Active' },
  { id: '4', name: 'Weekend Adult Batch', students: 6, avgAccuracy: '78%', avgPractice: '1.5 hrs/wk', pendingAssignments: 0, status: 'Active' },
];

export function Classes() {
  const navigate = useNavigate();

  return (
    <motion.div 
      className={styles.container}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <header className={styles.header}>
        <div>
          <h1 className={styles.title}>Classes</h1>
          <p className={styles.subtitle}>Manage your student groups and bulk assignments.</p>
        </div>
        <Button variant="primary" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Plus size={16} /> Create Class
        </Button>
      </header>

      <div className={styles.toolbar}>
        <div className={styles.searchBox}>
          <Search size={18} className={styles.searchIcon} />
          <input type="text" placeholder="Search classes..." className={styles.searchInput} />
        </div>
        <Button variant="secondary" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Filter size={16} /> Filter
        </Button>
      </div>

      <div className={styles.tableContainer}>
        <table className={styles.premiumTable}>
          <thead>
            <tr>
              <th>Class Name</th>
              <th>Students</th>
              <th>Avg Accuracy</th>
              <th>Avg Practice Time</th>
              <th>Pending Assignments</th>
              <th>Status</th>
              <th style={{ width: '40px' }}></th>
            </tr>
          </thead>
          <tbody>
            {mockClasses.map(cls => (
              <tr key={cls.id} onClick={() => navigate(`/teacher/classes/${cls.id}`)}>
                <td>
                  <div className={styles.classCell}>
                    <div className={styles.classIcon}>
                      <Layers size={18} />
                    </div>
                    <span className={styles.className}>{cls.name}</span>
                  </div>
                </td>
                <td>{cls.students}</td>
                <td>{cls.avgAccuracy}</td>
                <td>{cls.avgPractice}</td>
                <td>
                  {cls.pendingAssignments > 0 ? (
                    <span className={styles.assignmentBadge}>{cls.pendingAssignments} Active</span>
                  ) : (
                    <span className={styles.mutedText}>None</span>
                  )}
                </td>
                <td>
                  <span className={styles.statusBadge}>{cls.status}</span>
                </td>
                <td>
                  <button className={styles.actionBtn} onClick={(e) => { e.stopPropagation(); }}>
                    <MoreHorizontal size={18} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </motion.div>
  );
}
