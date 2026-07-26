import { useNavigate } from 'react-router-dom';
import { Plus, Upload, PlayCircle, Users, Sparkles, Check } from 'lucide-react';
import { motion } from 'framer-motion';
import { Button } from '../components/Button';
import styles from './TeacherDashboard.module.css';

const mockStudents = [
  { id: '1', name: 'Sarah Jenkins', avatar: 'S', lastActive: '2 hrs ago', lesson: 'Clair de Lune', time: '4.5 hrs', accuracy: '94%', status: 'On Track', statusColor: 'var(--status-success)' },
  { id: '2', name: 'Michael Chen', avatar: 'M', lastActive: '1 day ago', lesson: 'Für Elise', time: '2.1 hrs', accuracy: '82%', status: 'Needs Review', statusColor: 'var(--status-warning)' },
  { id: '3', name: 'Emma Watson', avatar: 'E', lastActive: '4 days ago', lesson: 'Canon in D', time: '0 hrs', accuracy: '--', status: 'Inactive', statusColor: 'var(--status-error)' },
  { id: '4', name: 'David Miller', avatar: 'D', lastActive: '5 hrs ago', lesson: 'Gymnopédie No.1', time: '3.2 hrs', accuracy: '89%', status: 'On Track', statusColor: 'var(--status-success)' },
];

export function TeacherDashboard() {
  const navigate = useNavigate();
  const date = new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' });

  return (
    <motion.div 
      className={styles.dashboard}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <header className={styles.hero}>
        <div>
          <h1 className={styles.greeting}>Good Morning, Sarah.</h1>
          <p className={styles.subtitle}>Here’s what’s happening in your classroom today.</p>
        </div>
        <div className={styles.dateBadge}>
          {date}
        </div>
      </header>

      <div className={styles.compactStats}>
        <div className={styles.statItem}>
          <span className={styles.statLabel}>Students</span>
          <span className={styles.statValue}>24</span>
        </div>
        <div className={styles.statDivider} />
        <div className={styles.statItem}>
          <span className={styles.statLabel}>Need Review</span>
          <span className={styles.statValue} style={{ color: 'var(--status-warning)' }}>12</span>
        </div>
        <div className={styles.statDivider} />
        <div className={styles.statItem}>
          <span className={styles.statLabel}>Avg Accuracy</span>
          <span className={styles.statValue}>85%</span>
        </div>
        <div className={styles.statDivider} />
        <div className={styles.statItem}>
          <span className={styles.statLabel}>Pending Assignments</span>
          <span className={styles.statValue}>8</span>
        </div>
      </div>

      <div className={styles.mainGrid}>
        {/* Left Column */}
        <div className={styles.leftCol}>
          <section className={styles.section}>
            <h2 className={styles.sectionTitle}>Quick Actions</h2>
            <div className={styles.actionGrid}>
              <div className={styles.actionCard} onClick={() => navigate('/teacher/assignments/create')}>
                <div className={styles.actionIcon}><Plus size={20} /></div>
                <div>
                  <h3>Create Assignment</h3>
                  <p>Assign a new exercise</p>
                </div>
              </div>
              <div className={styles.actionCard} onClick={() => navigate('/teacher/lessons/upload')}>
                <div className={styles.actionIcon}><Upload size={20} /></div>
                <div>
                  <h3>Upload Lesson</h3>
                  <p>Upload PDF or MIDI</p>
                </div>
              </div>
              <div className={styles.actionCard}>
                <div className={styles.actionIcon}><PlayCircle size={20} /></div>
                <div>
                  <h3>Review Performances</h3>
                  <p>12 awaiting review</p>
                </div>
              </div>
              <div className={styles.actionCard}>
                <div className={styles.actionIcon}><Users size={20} /></div>
                <div>
                  <h3>Add Student</h3>
                  <p>Invite new students</p>
                </div>
              </div>
            </div>
          </section>

          <section className={styles.section}>
            <div className={styles.sectionHeader}>
              <h2 className={styles.sectionTitle}>Student Activity</h2>
              <Button variant="ghost" style={{ padding: '0 8px' }} onClick={() => navigate('/teacher/students')}>View All</Button>
            </div>
            
            <div className={styles.tableContainer}>
              <table className={styles.premiumTable}>
                <thead>
                  <tr>
                    <th>Student</th>
                    <th>Current Lesson</th>
                    <th>Practice Time</th>
                    <th>Accuracy</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {mockStudents.map(student => (
                    <tr key={student.id} onClick={() => navigate(`/teacher/students/${student.id}`)}>
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
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </div>

        {/* Right Column */}
        <div className={styles.rightCol}>
          <section className={styles.section}>
            <div className={styles.aiCard}>
              <div className={styles.aiHeader}>
                <Sparkles size={20} color="var(--accent-primary)" />
                <h2 className={styles.sectionTitle} style={{ margin: 0 }}>AI Teaching Assistant</h2>
              </div>
              <p className={styles.aiSubtitle}>Students needing attention today:</p>
              
              <div className={styles.aiSuggestion}>
                <div className={styles.suggestionText}>
                  <strong>Michael Chen</strong>
                  <p>Rhythm accuracy dropped 8% over the last two sessions.</p>
                </div>
                <Button variant="secondary" style={{ width: '100%', display: 'flex', justifyContent: 'center', gap: '8px' }}>
                  <Plus size={16} /> Assign Rhythm Exercise
                </Button>
              </div>

              <div className={styles.aiSuggestion}>
                <div className={styles.suggestionText}>
                  <strong>David Miller</strong>
                  <p>Mastered all beginner lessons. Ready for advancement.</p>
                </div>
                <Button variant="primary" style={{ width: '100%', display: 'flex', justifyContent: 'center', gap: '8px' }}>
                  <Check size={16} /> Move to Intermediate
                </Button>
              </div>

              <div className={styles.aiSuggestion}>
                <div className={styles.suggestionText}>
                  <strong style={{ color: 'var(--status-error)' }}>Emma Watson</strong>
                  <p>No practice recorded for 4 days.</p>
                </div>
                <Button variant="secondary" style={{ width: '100%', display: 'flex', justifyContent: 'center', gap: '8px' }}>
                  Send Reminder
                </Button>
              </div>
            </div>
          </section>

          <section className={styles.section}>
            <div className={styles.sectionHeader}>
              <h2 className={styles.sectionTitle}>Recent Assignments</h2>
              <Button variant="ghost" style={{ padding: '0 8px' }} onClick={() => navigate('/teacher/assignments')}>View All</Button>
            </div>
            
            <div className={styles.assignmentList}>
              <div className={styles.assignmentItem}>
                <div>
                  <div className={styles.assignmentTitle}>C Major Scale Practice</div>
                  <div className={styles.assignmentMeta}>Due Tomorrow • Beginner Class</div>
                </div>
                <div className={styles.completionRate}>18/24 Done</div>
              </div>
              <div className={styles.assignmentItem}>
                <div>
                  <div className={styles.assignmentTitle}>Moonlight Sonata - Measure 1-15</div>
                  <div className={styles.assignmentMeta}>Due in 3 days • Sarah Jenkins</div>
                </div>
                <div className={styles.completionRate}>Pending</div>
              </div>
            </div>
          </section>
        </div>
      </div>
    </motion.div>
  );
}
