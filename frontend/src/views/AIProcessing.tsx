import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Sparkles, Check } from 'lucide-react';
import { motion } from 'framer-motion';
import styles from './AIProcessing.module.css';

export function AIProcessing() {
  const navigate = useNavigate();
  const [stepIndex, setStepIndex] = useState(0);

  const steps = [
    'Analyzing audio frequencies...',
    'Transcribing notes and rhythms...',
    'Identifying key signatures...',
    'Generating sheet music...',
    'Preparing AI practice plan...'
  ];

  useEffect(() => {
    const totalTime = 6000;
    const intervalTime = totalTime / steps.length;
    
    const interval = setInterval(() => {
      setStepIndex(prev => {
        if (prev < steps.length) return prev + 1;
        return prev;
      });
    }, intervalTime);

    const redirectTimer = setTimeout(() => {
      navigate('/song/generated-1');
    }, totalTime + 500);

    return () => {
      clearInterval(interval);
      clearTimeout(redirectTimer);
    };
  }, [navigate, steps.length]);

  const progress = Math.min((stepIndex / steps.length) * 100, 100);

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
          animate={{ rotate: 360 }}
          transition={{ duration: 10, repeat: Infinity, ease: "linear" }}
        >
          <Sparkles size={32} />
        </motion.div>
        
        <h2 className={styles.title}>Processing with AI</h2>
        <p className={styles.subtitle}>Our engine is transcribing your upload.</p>
        
        <div className={styles.progressContainer}>
          <div className={styles.progressBar}>
            <div className={styles.progressFill} style={{ width: `${progress}%` }}></div>
          </div>
          
          <div className={styles.steps}>
            {steps.map((step, idx) => {
              const isActive = idx === stepIndex;
              const isCompleted = idx < stepIndex;
              return (
                <div key={idx} className={`${styles.step} ${isActive ? styles.active : ''} ${isCompleted ? styles.completed : ''}`}>
                  <div className={styles.stepIcon}>
                    {isCompleted ? <Check size={14} /> : (isActive ? <Sparkles size={12} /> : null)}
                  </div>
                  <span>{step}</span>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
