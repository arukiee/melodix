import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { StudioTopBar } from '../components/Studio/StudioTopBar';
import { SheetMusic } from '../components/Studio/SheetMusic';
import { PracticeTimeline } from '../components/Studio/PracticeTimeline';
import { AICoach } from '../components/Studio/AICoach';
import { PianoKeyboard } from '../components/Studio/PianoKeyboard';
import { TransportBar } from '../components/Studio/TransportBar';
import styles from './Studio.module.css';

export function Studio() {
  const navigate = useNavigate();
  const [isFocusMode, setIsFocusMode] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playheadPos, setPlayheadPos] = useState(0); // 0 to 100

  // Mock playback loop
  useEffect(() => {
    let interval: any;
    if (isPlaying) {
      interval = setInterval(() => {
        setPlayheadPos(prev => {
          if (prev >= 100) {
            setIsPlaying(false);
            return 100;
          }
          return prev + 0.1;
        });
      }, 50);
    }
    return () => clearInterval(interval);
  }, [isPlaying]);

  const handleEndSession = () => {
    navigate('/summary/clair-de-lune');
  };

  const togglePlay = () => setIsPlaying(!isPlaying);

  return (
    <div className={styles.studioContainer}>
      {/* 1. Top Toolbar */}
      {!isFocusMode && (
        <StudioTopBar 
          isFocusMode={isFocusMode} 
          toggleFocusMode={() => setIsFocusMode(!isFocusMode)} 
        />
      )}

      {isFocusMode && (
        <div 
          style={{ position: 'absolute', top: '16px', right: '16px', zIndex: 100, cursor: 'pointer', background: 'var(--bg-elevated)', padding: '8px 16px', borderRadius: '20px', fontSize: '12px', border: '1px solid var(--border-color)' }}
          onClick={() => setIsFocusMode(false)}
        >
          Exit Focus Mode
        </div>
      )}

      {/* 2. Main Workspace */}
      <div className={styles.mainWorkspace}>
        <div className={styles.learningArea}>
          <SheetMusic />
          <PracticeTimeline playheadPos={playheadPos} />
        </div>
        
        {!isFocusMode && <AICoach />}
      </div>

      {/* 3. Bottom Piano & Transport */}
      <div className={styles.bottomArea}>
        <PianoKeyboard isPlaying={isPlaying} />
        <TransportBar 
          onEndSession={handleEndSession} 
          isPlaying={isPlaying} 
          onTogglePlay={togglePlay} 
        />
      </div>
    </div>
  );
}
