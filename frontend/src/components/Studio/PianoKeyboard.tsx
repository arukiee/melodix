import React, { useEffect, useState } from 'react';
import styles from './PianoKeyboard.module.css';

interface PianoKeyboardProps {
  isPlaying?: boolean;
}

export function PianoKeyboard({ isPlaying }: PianoKeyboardProps) {
  const [numKeys, setNumKeys] = useState(61);
  const [activeKeys, setActiveKeys] = useState<number[]>([]);

  useEffect(() => {
    let interval: any;
    if (isPlaying) {
      interval = setInterval(() => {
        // Randomly activate 1-3 keys
        const numActive = Math.floor(Math.random() * 3) + 1;
        const newKeys = Array.from({ length: numActive }).map(() => Math.floor(Math.random() * 20) + 20); // Central octave
        setActiveKeys(newKeys);
      }, 300);
    } else {
      setActiveKeys([]);
    }
    return () => clearInterval(interval);
  }, [isPlaying]);

  useEffect(() => {
    const updateKeys = () => {
      const width = window.innerWidth;
      if (width > 1200) setNumKeys(88);
      else if (width > 768) setNumKeys(61);
      else setNumKeys(49);
    };
    updateKeys();
    window.addEventListener('resize', updateKeys);
    return () => window.removeEventListener('resize', updateKeys);
  }, []);

  return (
    <div className={styles.container}>
      <div className={styles.scrollWrapper}>
        <div className={styles.keyboard}>
          {Array.from({ length: numKeys }).map((_, i) => {
            let keyClass = styles.whiteKey;
            
            // Basic logic to determine black keys (C major scale pattern)
            const noteInOctave = i % 12;
            const isBlack = [1, 3, 6, 8, 10].includes(noteInOctave);
            
            if (isBlack) keyClass = `${styles.blackKey}`;
            
            // Dynamic mock visual feedback
            if (activeKeys.includes(i)) {
              // 10% chance to simulate a wrong note for visual interest
              if (Math.random() > 0.9) {
                keyClass += ` ${styles.wrong}`;
              } else {
                keyClass += ` ${styles.correct}`;
              }
            } else if (!isPlaying) {
              // Static display when paused
              if (i === 24) keyClass += ` ${styles.correct}`;
              if (i === 26) keyClass += ` ${styles.wrong}`;
              if (i === 28) keyClass += ` ${styles.active}`;
            }
            
            return (
              <React.Fragment key={i}>
                <div className={keyClass} />
              </React.Fragment>
            );
          })}
        </div>
      </div>
    </div>
  );
}
