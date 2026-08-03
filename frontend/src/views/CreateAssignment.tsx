import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Loader2, CheckCircle } from 'lucide-react';
import { motion } from 'framer-motion';
import { Button } from '../components/Button';
import { Input } from '../components/Input';
import { apiClient } from '../api/client';
import styles from './CreateAssignment.module.css';

type Step = 'form' | 'processing' | 'success';

interface StudentOption {
  id: string;
  name: string;
}

export function CreateAssignment() {
  const navigate = useNavigate();
  const [step, setStep] = useState<Step>('form');
  const [error, setError] = useState('');

  // Form State
  const [title, setTitle] = useState('');
  const [targetStudentId, setTargetStudentId] = useState('');
  const [dueDate, setDueDate] = useState('');
  const [instructions, setInstructions] = useState('');
  const [students, setStudents] = useState<StudentOption[]>([]);
  const [isLoadingStudents, setIsLoadingStudents] = useState(true);

  useEffect(() => {
    const fetchStudents = async () => {
      try {
        const { data } = await apiClient.get('/social/friends');
        const formatted = data.map((f: any) => ({
          id: f.friend.id,
          name: f.friend.full_name || f.friend.email
        }));
        setStudents(formatted);
        if (formatted.length > 0) {
          setTargetStudentId(formatted[0].id);
        }
      } catch (err) {
        console.error('Failed to fetch students/friends:', err);
      } finally {
        setIsLoadingStudents(false);
      }
    };
    fetchStudents();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !dueDate) {
      setError('Please fill out all required fields.');
      return;
    }
    setError('');
    setStep('processing');
    
    try {
      await apiClient.post('/lessons', {
        title: title.trim(),
        description: instructions.trim() || `Due on ${dueDate}`,
        category: 'Assignment',
        difficulty: 'BEGINNER',
        estimated_duration: 20,
        is_published: true
      });
      setStep('success');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create assignment');
      setStep('form');
    }
  };

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <div className={styles.headerLeft}>
          <button className={styles.backBtn} onClick={() => navigate(-1)}>
            <ArrowLeft size={20} />
          </button>
          <div>
            <h1 className={styles.title}>Create Assignment</h1>
            <p className={styles.subtitle}>Assign lessons and exercises to your students.</p>
          </div>
        </div>
      </header>

      <div className={styles.card}>
        {step === 'form' && (
          <motion.form initial={{ opacity: 0 }} animate={{ opacity: 1 }} onSubmit={handleSubmit}>
            {error && <div className={styles.errorBanner}>{error}</div>}

            <div className={styles.formGroup}>
              <Input 
                label="Assignment Title" 
                placeholder="e.g. Moonlight Sonata Practice - Measure 1-15"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                required
              />
            </div>

            <div className={styles.formGrid}>
              <div className={styles.inputGroup}>
                <label className={styles.label}>Assign To (Student)</label>
                {isLoadingStudents ? (
                  <div style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Loading roster...</div>
                ) : students.length === 0 ? (
                  <select className={styles.select} disabled>
                    <option>No active friends/students found</option>
                  </select>
                ) : (
                  <select className={styles.select} value={targetStudentId} onChange={(e) => setTargetStudentId(e.target.value)}>
                    {students.map(s => (
                      <option key={s.id} value={s.id}>{s.name}</option>
                    ))}
                  </select>
                )}
              </div>

              <Input 
                label="Due Date" 
                type="date"
                value={dueDate}
                onChange={(e) => setDueDate(e.target.value)}
                required
              />
            </div>

            <div className={styles.formGroup}>
              <label className={styles.label}>Teacher Instructions (Optional)</label>
              <textarea 
                className={styles.textarea}
                placeholder="Add any specific notes or focus areas for the student..."
                value={instructions}
                onChange={(e) => setInstructions(e.target.value)}
              />
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '24px' }}>
              <Button type="button" variant="ghost" onClick={() => navigate(-1)}>Cancel</Button>
              <Button type="submit" variant="primary">Create & Send</Button>
            </div>
          </motion.form>
        )}

        {step === 'processing' && (
          <div style={{ textAlign: 'center', padding: '48px 0' }}>
            <Loader2 size={48} className="spin" color="var(--accent-primary)" />
            <h2 style={{ marginTop: '16px', fontSize: '18px' }}>Creating assignment...</h2>
          </div>
        )}

        {step === 'success' && (
          <div style={{ textAlign: 'center', padding: '48px 0' }}>
            <CheckCircle size={56} color="var(--status-success)" style={{ marginBottom: '16px' }} />
            <h2 style={{ fontSize: '24px', fontWeight: 600 }}>Assignment Created!</h2>
            <p style={{ color: 'var(--text-secondary)', marginTop: '8px', marginBottom: '24px' }}>
              The assignment has been successfully saved and sent.
            </p>
            <Button variant="primary" onClick={() => navigate('/teacher')}>
              Return to Teacher Dashboard
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
