import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Upload, PlayCircle, Users, Sparkles, Check, Bell, Loader2 } from 'lucide-react';
import { motion } from 'framer-motion';
import { Button } from '../components/Button';
import { useUser } from '../context/UserContext';
import { apiClient } from '../api/client';
import styles from './TeacherDashboard.module.css';

interface RosterStudent {
  id: string;
  name: string;
  email: string;
  avatar: string;
}

export function TeacherDashboard() {
  const navigate = useNavigate();
  const { profile } = useUser();
  const teacherName = profile.firstName || profile.full_name?.split(' ')[0] || profile.email?.split('@')[0] || 'Instructor';
  const date = new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' });

  const [students, setStudents] = useState<RosterStudent[]>([]);
  const [isLoadingStudents, setIsLoadingStudents] = useState(true);
  const [notification, setNotification] = useState<string | null>(null);

  useEffect(() => {
    const fetchStudents = async () => {
      setIsLoadingStudents(true);
      try {
        const { data } = await apiClient.get('/social/friends');
        const formatted = data.map((f: any) => {
          const name = f.friend.full_name || f.friend.email;
          const initial = name.charAt(0).toUpperCase();
          return {
            id: f.friend.id,
            name: name,
            email: f.friend.email,
            avatar: initial
          };
        });
        setStudents(formatted);
      } catch (err) {
        console.error('Failed to fetch teacher roster:', err);
      } finally {
        setIsLoadingStudents(false);
      }
    };

    fetchStudents();
  }, []);

  const showToast = (msg: string) => {
    setNotification(msg);
    setTimeout(() => setNotification(null), 3000);
  };

  const handleReviewPerformances = () => {
    navigate('/teacher/assignments');
  };

  const handleAddStudent = () => {
    navigate('/friends');
  };

  const handleAssignExercise = (studentName: string) => {
    navigate(`/teacher/assignments/create?title=${encodeURIComponent('Rhythm Exercise')}&student=${encodeURIComponent(studentName)}`);
  };

  const handleMoveToIntermediate = (studentName: string) => {
    showToast(`${studentName} moved to Intermediate level!`);
  };

  const handleSendReminder = (studentName: string) => {
    showToast(`Practice reminder sent to ${studentName}.`);
  };

  return (
    <motion.div 
      className={styles.dashboard}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      {notification && (
        <div style={{
          position: 'fixed', top: '24px', right: '24px', zIndex: 1000,
          background: 'var(--accent-primary)', color: '#fff',
          padding: '12px 20px', borderRadius: '8px', fontWeight: 600,
          boxShadow: '0 4px 12px rgba(0,0,0,0.2)'
        }}>
          {notification}
        </div>
      )}

      <header className={styles.hero}>
        <div>
          <h1 className={styles.greeting}>Good Morning, {teacherName}.</h1>
          <p className={styles.subtitle}>Here’s what’s happening in your classroom today.</p>
        </div>
        <div className={styles.dateBadge}>
          {date}
        </div>
      </header>

      <div className={styles.compactStats}>
        <div className={styles.statItem}>
          <span className={styles.statLabel}>Students</span>
          <span className={styles.statValue}>{students.length}</span>
        </div>
        <div className={styles.statDivider} />
        <div className={styles.statItem}>
          <span className={styles.statLabel}>Need Review</span>
          <span className={styles.statValue} style={{ color: 'var(--status-warning)' }}>2</span>
        </div>
        <div className={styles.statDivider} />
        <div className={styles.statItem}>
          <span className={styles.statLabel}>Avg Accuracy</span>
          <span className={styles.statValue}>92%</span>
        </div>
        <div className={styles.statDivider} />
        <div className={styles.statItem}>
          <span className={styles.statLabel}>Active Roster</span>
          <span className={styles.statValue}>{students.length > 0 ? 'Ready' : 'Setup'}</span>
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
              <div className={styles.actionCard} onClick={() => navigate('/upload')}>
                <div className={styles.actionIcon}><Upload size={20} /></div>
                <div>
                  <h3>Upload Lesson</h3>
                  <p>Upload PDF or MIDI</p>
                </div>
              </div>
              <div className={styles.actionCard} onClick={handleReviewPerformances}>
                <div className={styles.actionIcon}><PlayCircle size={20} /></div>
                <div>
                  <h3>Review Performances</h3>
                  <p>View assignments</p>
                </div>
              </div>
              <div className={styles.actionCard} onClick={handleAddStudent}>
                <div className={styles.actionIcon}><Users size={20} /></div>
                <div>
                  <h3>Add Student</h3>
                  <p>Connect with musicians</p>
                </div>
              </div>
            </div>
          </section>

          <section className={styles.section}>
            <div className={styles.sectionHeader}>
              <h2 className={styles.sectionTitle}>Student Roster ({students.length})</h2>
              <Button variant="ghost" style={{ padding: '0 8px' }} onClick={() => navigate('/friends')}>Manage Roster</Button>
            </div>
            
            <div className={styles.tableContainer}>
              {isLoadingStudents ? (
                <div style={{ textAlign: 'center', padding: '24px' }}>
                  <Loader2 size={24} className="spin" color="var(--accent-primary)" />
                </div>
              ) : students.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '24px', color: 'var(--text-secondary)' }}>
                  <p>No active students in roster. Use "Add Student" to connect with musicians.</p>
                </div>
              ) : (
                <table className={styles.premiumTable}>
                  <thead>
                    <tr>
                      <th>Student</th>
                      <th>Email</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {students.map(student => (
                      <tr key={student.id} onClick={() => navigate(`/friends`)}>
                        <td>
                          <div className={styles.studentCell}>
                            <div className={styles.avatarSm}>{student.avatar}</div>
                            <div>
                              <div className={styles.studentName}>{student.name}</div>
                            </div>
                          </div>
                        </td>
                        <td>{student.email}</td>
                        <td>
                          <span className={styles.statusBadge} style={{ color: 'var(--status-success)', backgroundColor: 'rgba(52,211,153,0.1)' }}>
                            Active Student
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
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
                <Button 
                  variant="secondary" 
                  onClick={() => handleAssignExercise('Michael Chen')}
                  style={{ width: '100%', display: 'flex', justifyContent: 'center', gap: '8px' }}
                >
                  <Plus size={16} /> Assign Rhythm Exercise
                </Button>
              </div>

              <div className={styles.aiSuggestion}>
                <div className={styles.suggestionText}>
                  <strong>David Miller</strong>
                  <p>Mastered all beginner lessons. Ready for advancement.</p>
                </div>
                <Button 
                  variant="primary" 
                  onClick={() => handleMoveToIntermediate('David Miller')}
                  style={{ width: '100%', display: 'flex', justifyContent: 'center', gap: '8px' }}
                >
                  <Check size={16} /> Move to Intermediate
                </Button>
              </div>

              <div className={styles.aiSuggestion}>
                <div className={styles.suggestionText}>
                  <strong style={{ color: 'var(--status-error)' }}>Emma Watson</strong>
                  <p>No practice recorded for 4 days.</p>
                </div>
                <Button 
                  variant="secondary" 
                  onClick={() => handleSendReminder('Emma Watson')}
                  style={{ width: '100%', display: 'flex', justifyContent: 'center', gap: '8px' }}
                >
                  <Bell size={16} /> Send Reminder
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
              <div className={styles.assignmentItem} onClick={() => navigate('/teacher/assignments')} style={{ cursor: 'pointer' }}>
                <div>
                  <div className={styles.assignmentTitle}>C Major Scale Practice</div>
                  <div className={styles.assignmentMeta}>Due Tomorrow • Beginner Class</div>
                </div>
                <div className={styles.completionRate}>18/24 Done</div>
              </div>
            </div>
          </section>
        </div>
      </div>
    </motion.div>
  );
}
