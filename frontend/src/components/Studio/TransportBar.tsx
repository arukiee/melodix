import { useState } from 'react';
import { Play, Pause, SkipBack, SkipForward, Repeat, Activity, Mic, MicOff } from 'lucide-react';
import styles from './TransportBar.module.css';

interface TransportBarProps {
  onEndSession: () => void;
  isPlaying?: boolean;
  onTogglePlay?: () => void;
}

export function TransportBar({ onEndSession, isPlaying, onTogglePlay }: TransportBarProps) {
  const [isRecording, setIsRecording] = useState(false);

  const toggleRecording = async () => {
    if (!isRecording) {
      try {
        await navigator.mediaDevices.getUserMedia({ audio: true });
        setIsRecording(true);
      } catch (err) {
        alert("Microphone access is required for practice recording and AI feedback.");
      }
    } else {
      setIsRecording(false);
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.leftGroup}>
        <div className={styles.tempoControl}>
          <span className={styles.label}>Tempo</span>
          <input type="range" min="50" max="150" defaultValue="100" className={styles.slider} />
          <span className={styles.value}>100%</span>
        </div>
      </div>
      
      <div className={styles.centerGroup}>
        <button className={styles.iconBtn} aria-label="Previous Measure">
          <SkipBack size={20} />
        </button>
        <button className={`${styles.iconBtn} ${styles.playBtn}`} onClick={onTogglePlay} aria-label={isPlaying ? "Pause" : "Play"}>
          {isPlaying ? <Pause size={24} fill="currentColor" /> : <Play size={24} fill="currentColor" />}
        </button>
        <button className={styles.iconBtn} aria-label="Next Measure">
          <SkipForward size={20} />
        </button>
      </div>

      <div className={styles.rightGroup}>
        <button 
          className={`${styles.iconBtn} ${isRecording ? styles.active : ''}`} 
          onClick={toggleRecording}
          aria-label="Microphone"
          title={isRecording ? "Recording active" : "Enable microphone"}
          style={isRecording ? { color: 'var(--status-error)' } : {}}
        >
          {isRecording ? <Mic size={20} /> : <MicOff size={20} />}
        </button>
        <button className={`${styles.iconBtn} ${styles.active}`} aria-label="Loop">
          <Repeat size={20} />
        </button>
        <button className={styles.iconBtn} aria-label="Metronome">
          <Activity size={20} />
        </button>
        <div className={styles.divider} />
        <button className={styles.endBtn} onClick={onEndSession}>
          End Session
        </button>
      </div>
    </div>
  );
}
