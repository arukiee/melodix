import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Loader2, CheckCircle } from 'lucide-react';
import { motion } from 'framer-motion';
import { Button } from '../components/Button';
import { Input } from '../components/Input';
import styles from './CreateAssignment.module.css';

type Step = 'form' | 'processing' | 'success';

export function CreateAssignment() {
  const navigate = useNavigate();
  const [step, setStep] = useState<Step>('form');
  const [error, setError] = useState('');

  // Form State
  const [title, setTitle] = useState('');
  const [target, setTarget] = useState('Sarah Jenkins');
  const [dueDate, setDueDate] = useState('');
  const [instructions, setInstructions] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title || !target || !dueDate) {
      setError('Please fill out all required fields.');
      return;
    }
    setError('');
    setStep('processing');
    
    // Simulate Network Request
    setTimeout(() => {
      setStep('success');
    }, 2000);
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
                placeholder="e.g. C Major Scale Practice"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                required
              />
            </div>

            <div className={styles.formGrid}>
              <div className={styles.inputGroup}>
                <label className={styles.label}>Assign To (Student or Class)</label>
                <select className={styles.select} value={target} onChange={(e) => setTarget(e.target.value)}>
                  <optgroup label="Students">
                    <option>Sarah Jenkins</option>
                    <option>Michael Chen</option>
                    <option>David Miller</option>
                  </optgroup>
                  <optgroup label="Classes">
                    <option>Beginner Piano</option>
                    <option>Intermediate Piano</option>
                  </optgroup>
                </select>
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

            <div className={styles.footer}>
              <Button variant="ghost" type="button" onClick={() => navigate(-1)}>Cancel</Button>
              <Button variant="primary" type="submit">Create Assignment</Button>
            </div>
          </motion.form>
        )}

        {step === 'processing' && (
          <motion.div className={styles.processingState} initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            <Loader2 size={48} className={styles.spinner} color="var(--accent-primary)" />
            <h2 className={styles.stepTitle}>Assigning Lesson...</h2>
            <p className={styles.mutedText}>Notifying students and updating their dashboards.</p>
          </motion.div>
        )}

        {step === 'success' && (
          <motion.div className={styles.successState} initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}>
            <CheckCircle size={64} color="var(--status-success)" style={{ marginBottom: '16px' }} />
            <h2 className={styles.stepTitle}>Assignment Created!</h2>
            <p className={styles.mutedText}>"{title}" has been successfully assigned to {target}.</p>
            <div className={styles.successActions}>
              <Button variant="secondary" onClick={() => {
                setTitle('');
                setDueDate('');
                setInstructions('');
                setStep('form');
              }}>Assign Another</Button>
              <Button variant="primary" onClick={() => navigate('/teacher/assignments')}>Back to Assignments</Button>
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
}
