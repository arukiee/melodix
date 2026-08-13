import { useState } from 'react';
import { TrendingUp, Compass, Upload } from 'lucide-react';
import { motion } from 'framer-motion';
import { PracticeWorkspace } from '../components/Studio/PracticeWorkspace';
import { PracticeAnalytics } from '../components/Learn/PracticeAnalytics';
import ImportSong from '../components/Learn/ImportSong';
import { PianoJourney } from '../components/Learn/PianoJourney';
import type { JourneyLevel, JourneyStep } from '../components/Learn/PianoJourney';
import type { PracticeMission } from '../api/practice';
import { useUser } from '../context/UserContext';
import styles from './Learn.module.css';

export function Learn() {
  const { profile } = useUser();
  const [activeTab, setActiveTab] = useState<'journey' | 'analytics' | 'import'>('journey');
  const [currentMission, setCurrentMission] = useState<PracticeMission | null>(null);
  const [currentSongTitle, setCurrentSongTitle] = useState('Piano Lesson');

  const handleStartStep = (level: JourneyLevel, step: JourneyStep) => {
    // Convert a JourneyStep into a PracticeMission for PracticeWorkspace
    const missionType = step.type === 'watch' ? 'listen'
      : step.type === 'right_hand' ? 'right_hand'
      : step.type === 'left_hand' ? 'left_hand'
      : step.type === 'both_hands' ? 'both_hands'
      : step.type === 'performance' ? 'performance'
      : 'listen';

    const mission: PracticeMission = {
      id: step.id,
      title: step.title,
      type: missionType,
      status: 'available',
      progress: 0,
      bpm: level.id <= 2 ? 60 : level.id <= 4 ? 72 : level.id <= 5 ? 80 : 90,
      expectedNotes: ['C4', 'D4', 'E4', 'F4', 'G4'],
      xpReward: step.xpReward,
      learningGoal: step.description,
    };

    setCurrentSongTitle(`Level ${level.id}: ${step.title}`);
    setCurrentMission(mission);
  };

  const handleCompleteMission = () => {
    setCurrentMission(null);
  };

  const tabBtnStyle = (active: boolean) => ({
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    padding: '8px 16px',
    fontSize: '0.85rem',
    fontWeight: 600,
    backgroundColor: active ? 'var(--accent-primary)' : 'transparent',
    color: active ? 'var(--bg-primary)' : 'var(--text-secondary)',
    border: 'none',
    borderRadius: '6px',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
  } as React.CSSProperties);

  return (
    <motion.div
      className={styles.learn}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      {/* Show PracticeWorkspace when a mission is active */}
      {currentMission ? (
        <PracticeWorkspace
          songTitle={currentSongTitle}
          mission={currentMission}
          onBack={() => setCurrentMission(null)}
          onComplete={handleCompleteMission}
        />
      ) : (
        <>
          <header className={styles.header} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
            <div>
              <h1 className={styles.title}>
                {activeTab === 'journey' ? '🎹 Piano Journey'
                  : activeTab === 'analytics' ? '📊 Progress Analytics'
                  : '📥 Import Song'}
              </h1>
              <p className={styles.subtitle}>
                {activeTab === 'journey'
                  ? `Welcome back, ${profile?.full_name?.split(' ')[0] || 'Musician'}. Continue your journey.`
                  : activeTab === 'analytics'
                  ? 'Your practice history and performance trends.'
                  : 'Add songs to your library from a file or online.'}
              </p>
            </div>

            <div style={{ display: 'flex', gap: '8px', backgroundColor: 'var(--bg-card)', padding: '4px', borderRadius: '10px', border: '1px solid var(--border-color)' }}>
              <button onClick={() => setActiveTab('journey')} style={tabBtnStyle(activeTab === 'journey')}>
                <Compass size={16} /> Journey
              </button>
              <button onClick={() => setActiveTab('analytics')} style={tabBtnStyle(activeTab === 'analytics')}>
                <TrendingUp size={16} /> Analytics
              </button>
              <button onClick={() => setActiveTab('import')} style={tabBtnStyle(activeTab === 'import')}>
                <Upload size={16} /> Import
              </button>
            </div>
          </header>

          <div style={{ marginTop: '8px' }}>
            {activeTab === 'journey' && (
              <PianoJourney onStartStep={handleStartStep} />
            )}
            {activeTab === 'analytics' && (
              <PracticeAnalytics />
            )}
            {activeTab === 'import' && (
              <ImportSong onImportSuccess={(_title) => setActiveTab('journey')} />

            )}
          </div>
        </>
      )}
    </motion.div>
  );
}
