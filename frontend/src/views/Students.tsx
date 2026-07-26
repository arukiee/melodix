import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Filter, Plus, ChevronRight } from 'lucide-react';
import { motion } from 'framer-motion';
import { Button } from '../components/Button';
import { Input } from '../components/Input';
import styles from './Students.module.css';

const mockStudents = [
  { id: '1', name: 'Sarah Jenkins', avatar: 'S', lastActive: '2 hrs ago', lesson: 'Clair de Lune', time: '4.5 hrs', accuracy: '94%', status: 'On Track', statusColor: 'var(--status-success)' },
  { id: '2', name: 'Michael Chen', avatar: 'M', lastActive: '1 day ago', lesson: 'Für Elise', time: '2.1 hrs', accuracy: '82%', status: 'Needs Review', statusColor: 'var(--status-warning)' },
  { id: '3', name: 'Emma Watson', avatar: 'E', lastActive: '4 days ago', lesson: 'Canon in D', time: '0 hrs', accuracy: '--', status: 'Inactive', statusColor: 'var(--status-error)' },
  { id: '4', name: 'David Miller', avatar: 'D', lastActive: '5 hrs ago', lesson: 'Gymnopédie No.1', time: '3.2 hrs', accuracy: '89%', status: 'On Track', statusColor: 'var(--status-success)' },
  { id: '5', name: 'Jessica Lee', avatar: 'J', lastActive: '2 days ago', lesson: 'Minuet in G', time: '1.5 hrs', accuracy: '85%', status: 'On Track', statusColor: 'var(--status-success)' },
];

export function Students() {
  const navigate = useNavigate();
  const [search, setSearch] = useState('');

  const filteredStudents = mockStudents.filter(s => s.name.toLowerCase().includes(search.toLowerCase()));

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <div>
          <h1 className={styles.title}>All Students</h1>
          <p className={styles.subtitle}>Manage your roster and track progress.</p>
        </div>
        <Button variant="primary">
          <Plus size={16} style={{ marginRight: '8px' }} />
          Add Student
        </Button>
      </header>

      <div className={styles.toolbar}>
        <div className={styles.searchWrap}>
          <Input 
            label=""
            placeholder="Search students..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <Button variant="secondary">
          <Filter size={16} style={{ marginRight: '8px' }} />
          Filter
        </Button>
      </div>

      <div className={styles.tableContainer}>
        {filteredStudents.length === 0 ? (
          <div className={styles.emptyState}>
            <h3>No students found</h3>
            <p>Try adjusting your search filters.</p>
          </div>
        ) : (
          <table className={styles.premiumTable}>
            <thead>
              <tr>
                <th>Student</th>
                <th>Current Lesson</th>
                <th>Practice Time (Week)</th>
                <th>Avg Accuracy</th>
                <th>Status</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {filteredStudents.map(student => (
                <motion.tr 
                  key={student.id} 
                  onClick={() => navigate(`/teacher/students/${student.id}`)}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  whileHover={{ backgroundColor: 'rgba(255,255,255,0.02)' }}
                >
                  <td>
                    <div className={styles.studentCell}>
                      <div className={styles.avatarSm}>{student.avatar}</div>
                      <div>
                        <div className={styles.studentName}>{student.name}</div>
                        <div className={styles.lastActive}>{student.lastActive}</div>
                      </div>
                    </div>
                  </td>
                  <td>{student.lesson}</td>
                  <td>{student.time}</td>
                  <td>{student.accuracy}</td>
                  <td>
                    <span className={styles.statusBadge} style={{ color: student.statusColor, backgroundColor: `color-mix(in srgb, ${student.statusColor} 10%, transparent)` }}>
                      {student.status}
                    </span>
                  </td>
                  <td>
                    <ChevronRight size={20} color="var(--text-muted)" />
                  </td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
