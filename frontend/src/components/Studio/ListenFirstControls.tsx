import React, { useState } from 'react';
import styles from './ListenFirstControls.module.css';
import { Play, Pause, FastForward, Rewind, Repeat, Volume2, Metronome } from 'lucide-react';

interface ListenFirstControlsProps {
  isPlaying: boolean;
  onPlayPause: () => void;
  playbackRate: number;
  onRateChange: (rate: number) => void;
  loopActive: boolean;
  onLoopToggle: () => void;
  metronomeActive: boolean;
  onMetronomeToggle: () => void;
  countInActive: boolean;
  onCountInToggle: () => void;
}

export function ListenFirstControls({
  isPlaying,
  onPlayPause,
  playbackRate,
  onRateChange,
  loopActive,
  onLoopToggle,
  metronomeActive,
  onMetronomeToggle,
  countInActive,
  onCountInToggle
}: ListenFirstControlsProps) {
  const rates = [0.5, 0.75, 1, 1.25, 1.5];

  return (
    <div className={styles.container}>
      <div className={styles.controlsGroup}>
        <button className={styles.iconBtn} onClick={onPlayPause} aria-label="Play/Pause">
          {isPlaying ? <Pause size={24} /> : <Play size={24} />}
        </button>
        
        <div className={styles.divider} />
        
        <div className={styles.rateSelector}>
          {rates.map(r => (
            <button
              key={r}
              className={`${styles.rateBtn} ${playbackRate === r ? styles.activeRate : ''}`}
              onClick={() => onRateChange(r)}
            >
              {r}x
            </button>
          ))}
        </div>
      </div>
      
      <div className={styles.controlsGroup}>
        <button 
          className={`${styles.iconBtn} ${loopActive ? styles.active : ''}`}
          onClick={onLoopToggle}
          title="Loop Section"
        >
          <Repeat size={20} />
        </button>
        <button 
          className={`${styles.iconBtn} ${metronomeActive ? styles.active : ''}`}
          onClick={onMetronomeToggle}
          title="Toggle Metronome"
        >
           {/* Replace icon with an SVG for Metronome or just text for now since lucide doesn't have a direct metronome */}
           <span style={{ fontWeight: 'bold' }}>M</span>
        </button>
        <button 
          className={`${styles.iconBtn} ${countInActive ? styles.active : ''}`}
          onClick={onCountInToggle}
          title="Count-In"
        >
          <span>1..2</span>
        </button>
      </div>
    </div>
  );
}
