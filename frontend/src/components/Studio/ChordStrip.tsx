import React from 'react';
import styles from './ChordStrip.module.css';
import { Play } from 'lucide-react';
import { audioEngine } from '../../services/audioEngine';

interface ChordDef {
  name: string;
  notes: string[];
  fingering?: string;
  difficulty: 'easy' | 'medium' | 'hard';
}

interface ChordStripProps {
  chords: ChordDef[];
  onChordClick?: (chord: ChordDef) => void;
}

export function ChordStrip({ chords, onChordClick }: ChordStripProps) {
  
  const handlePlay = async (chord: ChordDef, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!audioEngine.isInitialized()) {
      await audioEngine.init();
    }
    audioEngine.playChord(chord.notes);
  };

  const handleClick = (chord: ChordDef) => {
    if (onChordClick) {
      onChordClick(chord);
    }
  };

  return (
    <div className={styles.container}>
      <h3 className={styles.title}>Song Chords</h3>
      <div className={styles.chordList}>
        {chords.map((chord, idx) => (
          <div key={idx} className={styles.chordCard} onClick={() => handleClick(chord)}>
            <div className={styles.chordHeader}>
              <span className={styles.chordName}>{chord.name}</span>
              <span className={`${styles.badge} ${styles[chord.difficulty]}`}>
                {chord.difficulty}
              </span>
            </div>
            
            <div className={styles.chordBody}>
              <div className={styles.notesList}>
                {chord.notes.map((note, nIdx) => (
                  <span key={nIdx} className={styles.notePill}>{note}</span>
                ))}
              </div>
              {chord.fingering && (
                <div className={styles.fingering}>Fingers: {chord.fingering}</div>
              )}
            </div>

            <button className={styles.playBtn} onClick={(e) => handlePlay(chord, e)}>
              <Play size={16} /> Play
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
