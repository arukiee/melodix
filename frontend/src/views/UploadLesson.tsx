import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Upload as UploadIcon, FileAudio, Video, CheckCircle, ArrowRight, Loader2, ArrowLeft } from 'lucide-react';
import { motion } from 'framer-motion';
import { Button } from '../components/Button';
import { Input } from '../components/Input';
import styles from './UploadLesson.module.css';

type Step = 'source' | 'details' | 'processing' | 'success';

export function UploadLesson() {
  const navigate = useNavigate();
  const [step, setStep] = useState<Step>('source');
  const [sourceType, setSourceType] = useState<'file' | 'youtube' | null>(null);
  
  // Form State
  const [title, setTitle] = useState('');
  const [composer, setComposer] = useState('');
  const [level, setLevel] = useState('Beginner');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  const handleNext = () => {
    if (step === 'source' && sourceType) {
      setStep('details');
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title || !composer) {
      setError('Please fill out all required fields.');
      return;
    }
    setError('');
    setIsSubmitting(true);
    setStep('processing');
    
    // Simulate AI Processing
    setTimeout(() => {
      setStep('success');
      setIsSubmitting(false);
    }, 3000);
  };

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <div className={styles.headerLeft}>
          <button className={styles.backBtn} onClick={() => navigate(-1)}>
            <ArrowLeft size={20} />
          </button>
          <div>
            <h1 className={styles.title}>Upload Lesson</h1>
            <p className={styles.subtitle}>Add new repertoire to your library.</p>
          </div>
        </div>
      </header>

      <div className={styles.card}>
        {/* Progress Bar */}
        <div className={styles.progressTracker}>
          <div className={`${styles.stepDot} ${step === 'source' ? styles.activeDot : styles.completedDot}`} />
          <div className={`${styles.stepLine} ${step !== 'source' ? styles.completedLine : ''}`} />
          <div className={`${styles.stepDot} ${step === 'details' ? styles.activeDot : (step === 'processing' || step === 'success') ? styles.completedDot : ''}`} />
          <div className={`${styles.stepLine} ${(step === 'processing' || step === 'success') ? styles.completedLine : ''}`} />
          <div className={`${styles.stepDot} ${step === 'success' ? styles.completedDot : ''}`} />
        </div>

        {/* Step 1: Source */}
        {step === 'source' && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            <h2 className={styles.stepTitle}>Select Source</h2>
            <div className={styles.sourceOptions}>
              <div 
                className={`${styles.sourceBox} ${sourceType === 'file' ? styles.selectedBox : ''}`}
                onClick={() => setSourceType('file')}
              >
                <FileAudio size={32} />
                <h3>Upload File</h3>
                <p>PDF, MIDI, or MusicXML</p>
              </div>
              <div 
                className={`${styles.sourceBox} ${sourceType === 'youtube' ? styles.selectedBox : ''}`}
                onClick={() => setSourceType('youtube')}
              >
                <Video size={32} />
                <h3>YouTube Link</h3>
                <p>AI will extract the notes</p>
              </div>
            </div>
            <div className={styles.footer}>
              <Button variant="primary" disabled={!sourceType} onClick={handleNext}>
                Continue <ArrowRight size={16} style={{ marginLeft: '8px' }} />
              </Button>
            </div>
          </motion.div>
        )}

        {/* Step 2: Details */}
        {step === 'details' && (
          <motion.form initial={{ opacity: 0 }} animate={{ opacity: 1 }} onSubmit={handleSubmit}>
            <h2 className={styles.stepTitle}>Lesson Details</h2>
            {error && <div className={styles.errorBanner}>{error}</div>}
            
            {sourceType === 'youtube' && (
              <Input 
                label="YouTube URL" 
                placeholder="https://youtube.com/watch?v=..." 
                required 
              />
            )}
            
            {sourceType === 'file' && (
              <div className={styles.fileDrop}>
                <UploadIcon size={24} color="var(--text-muted)" />
                <p>Drag and drop your file here, or click to browse</p>
              </div>
            )}

            <div className={styles.formGrid}>
              <Input 
                label="Song Title" 
                value={title} 
                onChange={(e) => setTitle(e.target.value)} 
                required 
              />
              <Input 
                label="Composer / Artist" 
                value={composer} 
                onChange={(e) => setComposer(e.target.value)} 
                required 
              />
            </div>

            <div className={styles.inputGroup}>
              <label className={styles.label}>Difficulty Level</label>
              <select className={styles.select} value={level} onChange={(e) => setLevel(e.target.value)}>
                <option>Beginner</option>
                <option>Intermediate</option>
                <option>Advanced</option>
              </select>
            </div>

            <div className={styles.footer}>
              <Button variant="ghost" type="button" onClick={() => setStep('source')}>Back</Button>
              <Button variant="primary" type="submit">Upload & Process</Button>
            </div>
          </motion.form>
        )}

        {/* Step 3: Processing */}
        {step === 'processing' && (
          <motion.div className={styles.processingState} initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            <Loader2 size={48} className={styles.spinner} color="var(--accent-primary)" />
            <h2 className={styles.stepTitle}>Melodix AI is Processing...</h2>
            <p className={styles.mutedText}>Analyzing notes, tempo, and generating fingering suggestions.</p>
          </motion.div>
        )}

        {/* Step 4: Success */}
        {step === 'success' && (
          <motion.div className={styles.successState} initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}>
            <CheckCircle size={64} color="var(--status-success)" style={{ marginBottom: '16px' }} />
            <h2 className={styles.stepTitle}>Lesson Ready!</h2>
            <p className={styles.mutedText}>"{title}" has been successfully added to your library.</p>
            <div className={styles.successActions}>
              <Button variant="secondary" onClick={() => navigate('/teacher/assignments/create')}>Assign to Class</Button>
              <Button variant="primary" onClick={() => navigate('/teacher/lessons')}>Back to Library</Button>
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
}
