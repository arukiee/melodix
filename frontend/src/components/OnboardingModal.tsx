import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Keyboard, Laptop, Mic, Search, Star, Music, Award, Zap } from 'lucide-react';
import { useUser } from '../context/UserContext';
import styles from './OnboardingModal.module.css';

export function OnboardingModal() {
  const { isAuthenticated, isLoading } = useUser();
  const [isOpen, setIsOpen] = useState(false);
  const [step, setStep] = useState(1);
  const [selectedMethod, setSelectedMethod] = useState<string | null>(null);
  const [selectedExperience, setSelectedExperience] = useState<string | null>(null);

  useEffect(() => {
    if (isLoading || !isAuthenticated) {
      setIsOpen(false);
      return;
    }

    const hasCompletedOnboarding = localStorage.getItem('melodix_onboarding_complete');
    if (!hasCompletedOnboarding) {
      setIsOpen(true);
    }
  }, []);

  const handleMethodSelect = (method: string) => {
    setSelectedMethod(method);
    localStorage.setItem('melodix_input_method', method);
    
    // Depending on the method, prompt for permissions
    if (method === 'midi') {
      if (navigator.requestMIDIAccess) {
        navigator.requestMIDIAccess().catch(console.error);
      }
    } else if (method === 'acoustic') {
      navigator.mediaDevices.getUserMedia({ audio: true }).catch(console.error);
    }

    setTimeout(() => {
      setStep(2);
    }, 300);
  };

  const handleExperienceSelect = (exp: string) => {
    setSelectedExperience(exp);
    localStorage.setItem('melodix_experience', exp);
    localStorage.setItem('melodix_onboarding_complete', 'true');
    
    setTimeout(() => {
      setIsOpen(false);
    }, 400);
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <div className={styles.overlay}>
        <motion.div 
          className={styles.modal}
          initial={{ scale: 0.9, opacity: 0, y: 20 }}
          animate={{ scale: 1, opacity: 1, y: 0 }}
          exit={{ scale: 0.9, opacity: 0, y: 20 }}
          key={step}
        >
          {step === 1 && (
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
            >
              <h2 className={styles.title}>Welcome to Melodix</h2>
              <p className={styles.subtitle}>How will you be playing today?</p>
              
              <div className={styles.options}>
                <button 
                  className={`${styles.optionBtn} ${selectedMethod === 'laptop' ? styles.selected : ''}`}
                  onClick={() => handleMethodSelect('laptop')}
                >
                  <div className={styles.iconWrapper}><Laptop size={24} /></div>
                  <div className={styles.optionContent}>
                    <span className={styles.optionTitle}>Laptop Keyboard</span>
                    <span className={styles.optionDesc}>Play using your computer keys</span>
                  </div>
                </button>

                <button 
                  className={`${styles.optionBtn} ${selectedMethod === 'midi' ? styles.selected : ''}`}
                  onClick={() => handleMethodSelect('midi')}
                >
                  <div className={styles.iconWrapper}><Keyboard size={24} /></div>
                  <div className={styles.optionContent}>
                    <span className={styles.optionTitle}>MIDI Keyboard</span>
                    <span className={styles.optionDesc}>Connect via USB or Bluetooth</span>
                  </div>
                </button>

                <button 
                  className={`${styles.optionBtn} ${selectedMethod === 'acoustic' ? styles.selected : ''}`}
                  onClick={() => handleMethodSelect('acoustic')}
                >
                  <div className={styles.iconWrapper}><Mic size={24} /></div>
                  <div className={styles.optionContent}>
                    <span className={styles.optionTitle}>Real Piano</span>
                    <span className={styles.optionDesc}>Use your microphone to listen</span>
                  </div>
                </button>

                <button 
                  className={`${styles.optionBtn} ${selectedMethod === 'explore' ? styles.selected : ''}`}
                  onClick={() => handleMethodSelect('explore')}
                >
                  <div className={styles.iconWrapper}><Search size={24} /></div>
                  <div className={styles.optionContent}>
                    <span className={styles.optionTitle}>Just Exploring</span>
                    <span className={styles.optionDesc}>Look around without playing</span>
                  </div>
                </button>
              </div>
            </motion.div>
          )}

          {step === 2 && (
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
            >
              <h2 className={styles.title}>What's your experience?</h2>
              <p className={styles.subtitle}>We'll personalize your learning journey.</p>
              
              <div className={styles.options}>
                <button 
                  className={`${styles.optionBtn} ${selectedExperience === 'none' ? styles.selected : ''}`}
                  onClick={() => handleExperienceSelect('none')}
                >
                  <div className={styles.iconWrapper}><Star size={24} /></div>
                  <div className={styles.optionContent}>
                    <span className={styles.optionTitle}>Never played before</span>
                    <span className={styles.optionDesc}>Start from the absolute basics</span>
                  </div>
                </button>

                <button 
                  className={`${styles.optionBtn} ${selectedExperience === 'beginner' ? styles.selected : ''}`}
                  onClick={() => handleExperienceSelect('beginner')}
                >
                  <div className={styles.iconWrapper}><Music size={24} /></div>
                  <div className={styles.optionContent}>
                    <span className={styles.optionTitle}>Beginner</span>
                    <span className={styles.optionDesc}>I know a few notes and chords</span>
                  </div>
                </button>

                <button 
                  className={`${styles.optionBtn} ${selectedExperience === 'intermediate' ? styles.selected : ''}`}
                  onClick={() => handleExperienceSelect('intermediate')}
                >
                  <div className={styles.iconWrapper}><Award size={24} /></div>
                  <div className={styles.optionContent}>
                    <span className={styles.optionTitle}>Intermediate</span>
                    <span className={styles.optionDesc}>I can play songs with both hands</span>
                  </div>
                </button>

                <button 
                  className={`${styles.optionBtn} ${selectedExperience === 'advanced' ? styles.selected : ''}`}
                  onClick={() => handleExperienceSelect('advanced')}
                >
                  <div className={styles.iconWrapper}><Zap size={24} /></div>
                  <div className={styles.optionContent}>
                    <span className={styles.optionTitle}>Advanced</span>
                    <span className={styles.optionDesc}>I can read sheet music fluently</span>
                  </div>
                </button>
              </div>
            </motion.div>
          )}
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
