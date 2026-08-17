import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Sparkles, Check, AlertCircle } from 'lucide-react';
import { motion } from 'framer-motion';
import styles from './AIProcessing.module.css';
import { getPipelineStatus } from '../api/audio';
import type { ProcessingJobStatus } from '../api/audio';

// Map backend stages to UI steps
const STAGE_ORDER = [
  'queued',
  'validating',
  'preprocessing',
  'transcribing',
  'validating_notes',
  'analyzing_rhythm',
  'analyzing_chords',
  'assigning_hands',
  'computing_difficulty',
  'creating_lesson',
  'completed'
];

const STAGE_LABELS: Record<string, string> = {
  'queued': 'Waiting in queue...',
  'validating': 'Validating audio format...',
  'preprocessing': 'Preprocessing audio...',
  'transcribing': 'Transcribing with Basic Pitch...',
  'validating_notes': 'Validating notes and cleaning noise...',
  'analyzing_rhythm': 'Detecting BPM and rhythm...',
  'analyzing_chords': 'Identifying chords...',
  'assigning_hands': 'Assigning left/right hands...',
  'computing_difficulty': 'Generating difficulty variants...',
  'creating_lesson': 'Creating lesson structure...',
  'completed': 'Ready!',
};

export function AIProcessing() {
  const navigate = useNavigate();
  const { jobId } = useParams<{ jobId: string }>();
  const [status, setStatus] = useState<ProcessingJobStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!jobId) {
      setError("No job ID provided");
      return;
    }

    const poll = async () => {
      try {
        const data = await getPipelineStatus(jobId);
        
        // Normalize status to lowercase to match our frontend logic
        const normalizedStatus = (data.status || 'queued').toLowerCase();
        data.status = normalizedStatus;
        
        setStatus(data);

        if (normalizedStatus === 'completed') {
          // Add a small delay for the user to see 100% completion
          setTimeout(() => navigate(`/studio/${jobId}`), 1500);
        } else if (normalizedStatus === 'failed') {
          setError(data.stage_log[data.stage_log.length - 1]?.result || 'Processing failed');
        } else {
          // Keep polling
          setTimeout(poll, 1000);
        }
      } catch (err: any) {
        setError(err.message || "Failed to fetch status");
      }
    };

    poll();
  }, [jobId, navigate]);

  const progress = status?.progress_percent || 0;
  const currentStage = status?.status || 'queued';
  
  // Show a subset of major steps on the UI for cleaner visuals
  const displaySteps = [
    'validating',
    'transcribing',
    'analyzing_rhythm',
    'computing_difficulty',
    'completed'
  ];

  const currentStageIndex = STAGE_ORDER.indexOf(currentStage);

  return (
    <div className={styles.container}>
      <motion.div 
        className={styles.backgroundGlow}
        animate={{ scale: [1, 1.1, 1], opacity: [0.5, 0.8, 0.5] }}
        transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
      />
      
      <div className={styles.content}>
        <motion.div 
          className={styles.iconWrapper}
          animate={{ rotate: currentStage === 'completed' || error ? 0 : 360 }}
          transition={{ duration: 10, repeat: Infinity, ease: "linear" }}
        >
          {error ? <AlertCircle size={32} color="#ef4444" /> : <Sparkles size={32} />}
        </motion.div>
        
        <h2 className={styles.title}>
          {error ? 'Processing Failed' : 'Processing with AI'}
        </h2>
        <p className={styles.subtitle}>
          {error ? error : STAGE_LABELS[currentStage] || 'Our engine is transcribing your upload.'}
        </p>
        
        {!error && (
          <div className={styles.progressContainer}>
            <div className={styles.progressBar}>
              <div className={styles.progressFill} style={{ width: `${progress}%` }}></div>
            </div>
            
            <div className={styles.steps}>
              {displaySteps.map((step) => {
                const stepIndex = STAGE_ORDER.indexOf(step);
                const isActive = step === currentStage || (currentStageIndex > stepIndex && currentStageIndex < STAGE_ORDER.indexOf(displaySteps[displaySteps.indexOf(step) + 1] || 'completed'));
                const isCompleted = currentStageIndex > stepIndex || currentStage === 'completed';
                
                return (
                  <div key={step} className={`${styles.step} ${isActive ? styles.active : ''} ${isCompleted ? styles.completed : ''}`}>
                    <div className={styles.stepIcon}>
                      {isCompleted ? <Check size={14} /> : (isActive ? <Sparkles size={12} /> : null)}
                    </div>
                    <span>{STAGE_LABELS[step]}</span>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
