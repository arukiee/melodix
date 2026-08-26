import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronRight, ArrowRight, Check, Loader2, Sparkles, BookOpen, Music, Target } from 'lucide-react';
import { Button } from '../components/Button';
import { instrumentsApi, type Instrument } from '../api/instruments';
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
      navigate(profile.role === 'TEACHER' ? '/teacher' : '/dashboard');
    }
  }, [profile.isOnboardingComplete, profile.role, navigate]);
  
  // Form State
  const [accountType, setAccountType] = useState<AccountType | null>(null);
  const [experience, setExperience] = useState<string | null>(null);
  const [genres, setGenres] = useState<string[]>([]);
  const [practiceTime, setPracticeTime] = useState<string | null>(null);
  const [instrument, setInstrument] = useState<string | null>(null);
  const [instruments, setInstruments] = useState<Instrument[]>([]);
  const [takeAssessment, setTakeAssessment] = useState<boolean | null>(null);

  // Loading animation state
  const [loadingStep, setLoadingStep] = useState(0);

  // Fetch instruments from backend when component mounts, with fallback
  useEffect(() => {
    const defaultInstruments: Instrument[] = [
      { id: 'piano', name: 'Grand Piano' },
      { id: 'upright', name: 'Upright Piano' },
      { id: 'digital', name: 'Digital Piano' },
      { id: 'keyboard', name: 'MIDI Keyboard' },
      { id: 'synth', name: 'Synthesizer' },
    ];
    const fetchInstruments = async () => {
      try {
        const data = await instrumentsApi.getInstruments();
        setInstruments(data.length > 0 ? data : defaultInstruments);
      } catch (err) {
        console.warn('Instruments API unavailable, using defaults', err);
        setInstruments(defaultInstruments);
      }
    };
    fetchInstruments();
  }, []);

  const nextStep = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(prev => prev + 1);
    }
  };

  useEffect(() => {
    if (currentStep === 7) {
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
      }, 1200);
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

  const isTeacher = accountType === 'teacher';

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
        Let’s personalize your piano experience.<br/>
        This takes under 2 minutes.
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

  const renderExperience = () => {
    const studentExp = ['I’ve never played before', 'Beginner', 'Intermediate', 'Advanced'];
    const teacherExp = ['Beginner Students', 'Intermediate Students', 'Advanced Students', 'All Skill Levels'];
    const options = isTeacher ? teacherExp : studentExp;

    return (
      <motion.div
        key="experience"
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        exit={{ opacity: 0, x: -20 }}
      >
        <div className={styles.header}>
          <h1 className={styles.title}>{isTeacher ? 'Target Student Level' : 'Your Experience'}</h1>
          <p className={styles.subtitle}>
            {isTeacher ? 'What is your primary teaching level?' : 'How much piano experience do you have?'}
          </p>
        </div>
        <div className={styles.optionsGrid}>
          {options.map(exp => (
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
  };

  const renderGenres = () => {
    const studentList = ['Classical', 'Pop', 'Anime', 'Movie Soundtracks', 'Game Music', 'Jazz', 'Worship', 'Original Songs'];
    const teacherList = ['Classical Piano', 'Modern & Jazz', 'Sight Reading', 'Music Theory', 'Pop Accompaniment', 'Technique Drills'];
    const genreList = isTeacher ? teacherList : studentList;

    return (
      <motion.div
        key="genres"
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        exit={{ opacity: 0, x: -20 }}
      >
        <div className={styles.header}>
          <h1 className={styles.title}>{isTeacher ? 'Teaching Focus' : 'What would you like to learn?'}</h1>
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

  const renderPractice = () => {
    const studentTimes = ['10 minutes', '20 minutes', '30 minutes', '45 minutes', '60+ minutes'];
    const teacherSizes = ['1–5 Students', '5–15 Students', '15–30 Students', '30+ Students'];
    const options = isTeacher ? teacherSizes : studentTimes;

    return (
      <motion.div
        key="practice"
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        exit={{ opacity: 0, x: -20 }}
      >
        <div className={styles.header}>
          <h1 className={styles.title}>{isTeacher ? 'Studio Roster Size' : 'Daily Goal'}</h1>
          <p className={styles.subtitle}>
            {isTeacher ? 'How many active students do you manage?' : 'How much would you like to practice each day?'}
          </p>
        </div>
        <div className={styles.optionsGrid}>
          {options.map(time => (
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
  };

  const renderInstrument = () => {
    // Determine which instruments to show based on role
    const filtered = instruments.filter(() => true);
    const options = isTeacher ? filtered : filtered;

    return (
      <motion.div
        key="instrument"
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        exit={{ opacity: 0, x: -20 }}
      >
        <div className={styles.header}>
          <h1 className={styles.title}>{isTeacher ? 'Studio Equipment' : 'Your Instrument'}</h1>
          <p className={styles.subtitle}>
            {isTeacher ? 'What setup do you use in your studio?' : 'What instrument will you use?'}
          </p>
        </div>
        <div className={styles.optionsGrid}>
          {options.map(inst => (
            <div 
              key={inst.id}
              className={`${styles.optionCard} ${instrument === inst.name ? styles.selected : ''}`}
              onClick={() => setInstrument(inst.name)}
            >
              <div className={styles.optionTitle}>{inst.name}</div>
            </div>
          ))}
        </div>
      </motion.div>
    );
  };

  const renderAssessment = () => (
    <motion.div
      key="assessment"
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -20 }}
    >
      <div className={styles.header}>
        <Sparkles size={48} color="var(--accent-primary)" style={{ marginBottom: '24px' }} />
        <h1 className={styles.title}>{isTeacher ? 'AI Teaching Diagnostics' : 'AI Skill Assessment'}</h1>
        <p className={styles.subtitle}>
          {isTeacher ? 'Enable AI feedback & automated student progress reports?' : 'Would you like Melodix to assess your current skill level?'}
        </p>
      </div>
      <div className={styles.optionsGrid}>
        <div 
          className={`${styles.optionCard} ${takeAssessment === true ? styles.selected : ''}`}
          onClick={() => setTakeAssessment(true)}
        >
          <div className={styles.optionTitle}>{isTeacher ? 'Enable AI Assistant' : "Yes, let's do it"}</div>
          <div className={styles.optionDescription}>
            {isTeacher ? 'Automate rhythm diagnostics and assignment tracking.' : 'Play a short piece to calibrate your level.'}
          </div>
        </div>
        <div 
          className={`${styles.optionCard} ${takeAssessment === false ? styles.selected : ''}`}
          onClick={() => setTakeAssessment(false)}
        >
          <div className={styles.optionTitle}>Skip for now</div>
          <div className={styles.optionDescription}>
            {isTeacher ? 'Use manual studio management.' : "We'll generate a default beginner roadmap."}
          </div>
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
        <p className={styles.subtitle}>Setting up your customized Melodix workspace.</p>
      </div>
      
      <div className={styles.loadingList}>
        <div className={`${styles.loadingItem} ${loadingStep >= 1 ? styles.completed : (loadingStep === 0 ? styles.active : '')}`}>
          {loadingStep >= 1 ? <Check size={20} /> : <BookOpen size={20} />}
          {isTeacher ? 'Configuring teacher studio dashboard' : 'Creating your lesson roadmap'}
        </div>
        <div className={`${styles.loadingItem} ${loadingStep >= 2 ? styles.completed : (loadingStep === 1 ? styles.active : '')}`}>
          {loadingStep >= 2 ? <Check size={20} /> : <Target size={20} />}
          {isTeacher ? 'Preparing student assignment tools' : 'Selecting initial exercises'}
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
            {Array.from({ length: 6 }).map((_, i) => (
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
