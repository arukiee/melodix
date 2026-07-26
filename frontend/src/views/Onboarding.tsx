import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronRight, ArrowRight, Check, Loader2, Sparkles, BookOpen, Music, Target } from 'lucide-react';
import { Button } from '../components/Button';
import type { AccountType } from '../context/UserContext';
import { useUser } from '../context/UserContext';
import styles from './Onboarding.module.css';

const steps = [
  'Welcome',
  'Account',
  'Experience',
  'Genres',
  'Practice',
  'Instrument',
  'Assessment',
  'Generating'
];

export function Onboarding() {
  const navigate = useNavigate();
  const { profile, completeOnboarding } = useUser();
  const [currentStep, setCurrentStep] = useState(0);

  // If already onboarded, redirect away from onboarding
  useEffect(() => {
    if (profile.isOnboardingComplete) {
      navigate('/dashboard');
    }
  }, [profile.isOnboardingComplete, navigate]);
  
  // Form State
  const [accountType, setAccountType] = useState<AccountType | null>(null);
  const [experience, setExperience] = useState<string | null>(null);
  const [genres, setGenres] = useState<string[]>([]);
  const [practiceTime, setPracticeTime] = useState<string | null>(null);
  const [instrument, setInstrument] = useState<string | null>(null);
  const [takeAssessment, setTakeAssessment] = useState<boolean | null>(null);

  // Loading animation state
  const [loadingStep, setLoadingStep] = useState(0);

  const nextStep = () => {
    // If account type is strictly Teacher, skip Experience, Genres, Practice, Instrument, Assessment
    if (currentStep === 1 && accountType === 'teacher') {
      setCurrentStep(7); // Jump straight to Generation
      return;
    }
    if (currentStep < steps.length - 1) {
      setCurrentStep(prev => prev + 1);
    }
  };

  useEffect(() => {
    if (currentStep === 7) {
      // Simulate loading process
      const interval = setInterval(() => {
        setLoadingStep(prev => {
          if (prev >= 3) {
            clearInterval(interval);
            setTimeout(() => {
              completeOnboarding(accountType || 'student', {
                pianoExperience: experience || '',
                favoriteGenres: genres,
                dailyPracticeGoal: practiceTime || '',
                defaultInstrument: instrument || 'Grand Piano',
                metronomeVolume: 80,
              });
              navigate(accountType === 'teacher' ? '/teacher' : '/dashboard');
            }, 1000);
            return prev;
          }
          return prev + 1;
        });
      }, 1500);
      return () => clearInterval(interval);
    }
  }, [currentStep, accountType, experience, genres, practiceTime, instrument, completeOnboarding, navigate]);

  const toggleGenre = (genre: string) => {
    setGenres(prev => 
      prev.includes(genre) 
        ? prev.filter(g => g !== genre)
        : [...prev, genre]
    );
  };

  const renderWelcome = () => (
    <motion.div
      key="welcome"
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -20 }}
      className={styles.header}
      style={{ marginTop: '48px' }}
    >
      <Music size={48} color="var(--accent-primary)" style={{ marginBottom: '24px' }} />
      <h1 className={styles.title}>Welcome to Melodix</h1>
      <p className={styles.subtitle} style={{ marginBottom: '48px' }}>
        Let’s personalize your piano learning experience.<br/>
        This only takes about 2 minutes.
      </p>
      <Button variant="primary" onClick={nextStep} style={{ padding: '16px 32px', fontSize: '16px' }}>
        Get Started <ArrowRight size={20} style={{ marginLeft: '8px' }} />
      </Button>
    </motion.div>
  );

  const renderAccountType = () => (
    <motion.div
      key="account"
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -20 }}
    >
      <div className={styles.header}>
        <h1 className={styles.title}>Choose Account Type</h1>
        <p className={styles.subtitle}>First, tell us how you’ll be using Melodix.</p>
      </div>
      <div className={styles.optionsGrid}>
        <div 
          className={`${styles.optionCard} ${accountType === 'student' ? styles.selected : ''}`}
          onClick={() => setAccountType('student')}
        >
          <div className={styles.optionTitle}>Student</div>
          <div className={styles.optionDescription}>I want to learn piano with AI.</div>
        </div>
        <div 
          className={`${styles.optionCard} ${accountType === 'teacher' ? styles.selected : ''}`}
          onClick={() => setAccountType('teacher')}
        >
          <div className={styles.optionTitle}>Teacher</div>
          <div className={styles.optionDescription}>I want to teach and manage students.</div>
        </div>
        <div 
          className={`${styles.optionCard} ${accountType === 'both' ? styles.selected : ''}`}
          onClick={() => setAccountType('both')}
        >
          <div className={styles.optionTitle}>Both</div>
          <div className={styles.optionDescription}>I’ll be learning and teaching.</div>
        </div>
      </div>
    </motion.div>
  );

  const renderExperience = () => (
    <motion.div
      key="experience"
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -20 }}
    >
      <div className={styles.header}>
        <h1 className={styles.title}>Your Experience</h1>
        <p className={styles.subtitle}>How much piano experience do you have?</p>
      </div>
      <div className={styles.optionsGrid}>
        {['I’ve never played before', 'Beginner', 'Intermediate', 'Advanced'].map(exp => (
          <div 
            key={exp}
            className={`${styles.optionCard} ${experience === exp ? styles.selected : ''}`}
            onClick={() => setExperience(exp)}
          >
            <div className={styles.optionTitle}>{exp}</div>
          </div>
        ))}
      </div>
    </motion.div>
  );

  const renderGenres = () => {
    const genreList = ['Classical', 'Pop', 'Anime', 'Movie Soundtracks', 'Game Music', 'Jazz', 'Worship', 'Original Songs'];
    return (
      <motion.div
        key="genres"
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        exit={{ opacity: 0, x: -20 }}
      >
        <div className={styles.header}>
          <h1 className={styles.title}>What would you like to learn?</h1>
          <p className={styles.subtitle}>Select all that apply.</p>
        </div>
        <div className={styles.optionsGridMulti}>
          {genreList.map(genre => (
            <div 
              key={genre}
              className={`${styles.optionCard} ${genres.includes(genre) ? styles.selected : ''}`}
              onClick={() => toggleGenre(genre)}
              style={{ alignItems: 'center', textAlign: 'center', padding: '16px' }}
            >
              <div className={styles.optionTitle}>{genre}</div>
            </div>
          ))}
        </div>
      </motion.div>
    );
  };

  const renderPractice = () => (
    <motion.div
      key="practice"
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -20 }}
    >
      <div className={styles.header}>
        <h1 className={styles.title}>Daily Goal</h1>
        <p className={styles.subtitle}>How much would you like to practice each day?</p>
      </div>
      <div className={styles.optionsGrid}>
        {['10 minutes', '20 minutes', '30 minutes', '45 minutes', '60+ minutes'].map(time => (
          <div 
            key={time}
            className={`${styles.optionCard} ${practiceTime === time ? styles.selected : ''}`}
            onClick={() => setPracticeTime(time)}
          >
            <div className={styles.optionTitle}>{time}</div>
          </div>
        ))}
      </div>
    </motion.div>
  );

  const renderInstrument = () => (
    <motion.div
      key="instrument"
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -20 }}
    >
      <div className={styles.header}>
        <h1 className={styles.title}>Your Instrument</h1>
        <p className={styles.subtitle}>What instrument will you use?</p>
      </div>
      <div className={styles.optionsGrid}>
        {['MIDI Keyboard', 'Digital Piano', 'Acoustic Piano', 'GarageBand', 'Virtual Keyboard'].map(inst => (
          <div 
            key={inst}
            className={`${styles.optionCard} ${instrument === inst ? styles.selected : ''}`}
            onClick={() => setInstrument(inst)}
          >
            <div className={styles.optionTitle}>{inst}</div>
          </div>
        ))}
      </div>
    </motion.div>
  );

  const renderAssessment = () => (
    <motion.div
      key="assessment"
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -20 }}
    >
      <div className={styles.header}>
        <Sparkles size={48} color="var(--accent-primary)" style={{ marginBottom: '24px' }} />
        <h1 className={styles.title}>AI Skill Assessment</h1>
        <p className={styles.subtitle}>Would you like Melodix to assess your current skill level?</p>
      </div>
      <div className={styles.optionsGrid}>
        <div 
          className={`${styles.optionCard} ${takeAssessment === true ? styles.selected : ''}`}
          onClick={() => setTakeAssessment(true)}
        >
          <div className={styles.optionTitle}>Yes, let's do it</div>
          <div className={styles.optionDescription}>Play a short piece to calibrate your level.</div>
        </div>
        <div 
          className={`${styles.optionCard} ${takeAssessment === false ? styles.selected : ''}`}
          onClick={() => setTakeAssessment(false)}
        >
          <div className={styles.optionTitle}>Skip for now</div>
          <div className={styles.optionDescription}>We'll generate a default beginner roadmap.</div>
        </div>
      </div>
    </motion.div>
  );

  const renderGenerating = () => (
    <motion.div
      key="generating"
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className={styles.loadingScreen}
    >
      <Loader2 size={48} className="spin" color="var(--accent-primary)" />
      <div>
        <h1 className={styles.title} style={{ marginBottom: '8px' }}>Building your experience...</h1>
        <p className={styles.subtitle}>This should only take a few seconds.</p>
      </div>
      
      <div className={styles.loadingList}>
        <div className={`${styles.loadingItem} ${loadingStep >= 1 ? styles.completed : (loadingStep === 0 ? styles.active : '')}`}>
          {loadingStep >= 1 ? <Check size={20} /> : <BookOpen size={20} />}
          Creating your lesson roadmap
        </div>
        <div className={`${styles.loadingItem} ${loadingStep >= 2 ? styles.completed : (loadingStep === 1 ? styles.active : '')}`}>
          {loadingStep >= 2 ? <Check size={20} /> : <Target size={20} />}
          Selecting initial exercises
        </div>
        <div className={`${styles.loadingItem} ${loadingStep >= 3 ? styles.completed : (loadingStep === 2 ? styles.active : '')}`}>
          {loadingStep >= 3 ? <Check size={20} /> : <Sparkles size={20} />}
          Preparing AI recommendations
        </div>
      </div>
    </motion.div>
  );

  const canProceed = () => {
    switch (currentStep) {
      case 0: return true;
      case 1: return accountType !== null;
      case 2: return experience !== null;
      case 3: return genres.length > 0;
      case 4: return practiceTime !== null;
      case 5: return instrument !== null;
      case 6: return takeAssessment !== null;
      default: return false;
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.glow} />
      <div className={styles.card}>
        
        {currentStep > 0 && currentStep < 7 && (
          <div className={styles.stepper} style={{ position: 'absolute', top: '32px', left: '50%', transform: 'translateX(-50%)' }}>
            {Array.from({ length: accountType === 'teacher' ? 1 : 6 }).map((_, i) => (
              <div key={i} className={`${styles.stepDot} ${currentStep === i + 1 ? styles.active : ''}`} />
            ))}
          </div>
        )}

        <div style={{ flex: 1 }}>
          <AnimatePresence mode="wait">
            {currentStep === 0 && renderWelcome()}
            {currentStep === 1 && renderAccountType()}
            {currentStep === 2 && renderExperience()}
            {currentStep === 3 && renderGenres()}
            {currentStep === 4 && renderPractice()}
            {currentStep === 5 && renderInstrument()}
            {currentStep === 6 && renderAssessment()}
            {currentStep === 7 && renderGenerating()}
          </AnimatePresence>
        </div>

        {currentStep > 0 && currentStep < 7 && (
          <div className={styles.actions}>
            <Button variant="ghost" onClick={() => setCurrentStep(prev => prev - 1)}>
              Back
            </Button>
            <Button variant="primary" onClick={nextStep} disabled={!canProceed()}>
              {currentStep === 6 ? 'Complete' : 'Continue'} <ChevronRight size={16} style={{ marginLeft: '4px' }} />
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
