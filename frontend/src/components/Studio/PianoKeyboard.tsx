import React, { useEffect, useMemo, useState, useRef } from 'react';
import styles from './PianoKeyboard.module.css';
import type { TimelineNote } from '../../services/timeline';
import { audioEngine } from '../../services/audioEngine';
import { keyboardMapper } from '../../services/keyboardMapper';

interface PianoKeyboardProps {
  isPlaying?: boolean;
  timelineNotes?: TimelineNote[];
  highlightNotes?: string[];
  highlightedNotes?: string[];
  onNotePlay?: (note: string) => void;
}

const EMPTY_TIMELINE_NOTES: TimelineNote[] = [];
const EMPTY_HIGHLIGHT_NOTES: string[] = [];

export function PianoKeyboard({ isPlaying, timelineNotes = EMPTY_TIMELINE_NOTES, highlightNotes, highlightedNotes, onNotePlay }: PianoKeyboardProps) {
  const activeHighlights = highlightNotes ?? highlightedNotes ?? EMPTY_HIGHLIGHT_NOTES;
  const [numKeys, setNumKeys] = useState(61);
  const [activeKeys, setActiveKeys] = useState<Set<number>>(new Set());
  const isMouseDown = useRef(false);
  const onNotePlayRef = useRef(onNotePlay);
  onNotePlayRef.current = onNotePlay;
  const currentKeyMap = useMemo(() => keyboardMapper.generateMapping(timelineNotes), [timelineNotes]);

  useEffect(() => {
    const updateKeys = () => {
      const width = window.innerWidth;
      if (width > 1200) setNumKeys(88);
      else if (width > 768) setNumKeys(61);
      else setNumKeys(49);
    };
    updateKeys();
    window.addEventListener('resize', updateKeys);
    
    const handleMouseUp = () => {
      isMouseDown.current = false;
      setActiveKeys(new Set()); // Clear active keys on global mouse up
    };
    window.addEventListener('mouseup', handleMouseUp);
    window.addEventListener('touchend', handleMouseUp);
    
    return () => {
      window.removeEventListener('resize', updateKeys);
      window.removeEventListener('mouseup', handleMouseUp);
      window.removeEventListener('touchend', handleMouseUp);
    };
  }, []);

  const getMidiNoteIndex = (midiName: string): number => {
    return keyboardMapper.getMidiNoteIndex(midiName);
  };

  const getNoteNameFromIndex = (index: number): string => {
    return keyboardMapper.getNoteNameFromIndex(index);
  };

  useEffect(() => {
    const handleKeyDown = async (e: KeyboardEvent) => {
      if (e.repeat) return;
      const index = currentKeyMap[e.key.toLowerCase()];
      if (index !== undefined) {
        if (!audioEngine.isInitialized()) await audioEngine.init();
        const noteName = getNoteNameFromIndex(index);
        audioEngine.playNote(noteName);
        setActiveKeys(prev => new Set(prev).add(index));
        onNotePlayRef.current?.(noteName);
      }
    };

    const handleKeyUp = (e: KeyboardEvent) => {
      const index = currentKeyMap[e.key.toLowerCase()];
      if (index !== undefined) {
        setActiveKeys(prev => {
          const next = new Set(prev);
          next.delete(index);
          return next;
        });
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('keyup', handleKeyUp);

    // MIDI Support
    const handleMidiMessage = async (message: any) => {
      const [command, note, velocity] = message.data;
      if (command === 144 && velocity > 0) { // Note on
        const index = note - 24; // C4 is 60 in MIDI, 36 in our index. 60 - 24 = 36.
        if (index >= 0 && index < numKeys) {
          if (!audioEngine.isInitialized()) await audioEngine.init();
          const noteName = getNoteNameFromIndex(index);
          audioEngine.playNote(noteName, velocity / 127);
          setActiveKeys(prev => new Set(prev).add(index));
          onNotePlayRef.current?.(noteName);
        }
      } else if (command === 128 || (command === 144 && velocity === 0)) { // Note off
        const index = note - 24;
        if (index >= 0 && index < numKeys) {
          setActiveKeys(prev => {
            const next = new Set(prev);
            next.delete(index);
            return next;
          });
        }
      } else if (command === 176 && note === 64) { // Control Change: Sustain Pedal (CC 64)
        const isSustainOn = velocity >= 64;
        console.log('Sustain Pedal:', isSustainOn ? 'ON' : 'OFF');
        // Future: Pass sustain state to audioEngine if needed
      }
    };

    let disposed = false;
    if (navigator.requestMIDIAccess) {
      navigator.requestMIDIAccess().then(midiAccess => {
        if (disposed) return;
        midiAccess.inputs.forEach(input => {
          input.onmidimessage = handleMidiMessage;
        });
      }).catch(err => console.log('MIDI Access failed', err));
    }

    return () => {
      disposed = true;
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('keyup', handleKeyUp);
      if (navigator.requestMIDIAccess) {
        navigator.requestMIDIAccess().then(midiAccess => {
          midiAccess.inputs.forEach(input => { input.onmidimessage = null; });
        }).catch(() => undefined);
      }
    };
  }, [numKeys, currentKeyMap]);

  const handleKeyInteraction = async (index: number, type: 'down' | 'enter') => {
    if (type === 'enter' && !isMouseDown.current) return;
    if (type === 'down') {
      isMouseDown.current = true;
    }
    
    if (!audioEngine.isInitialized()) {
      await audioEngine.init();
    }
    
    const noteName = getNoteNameFromIndex(index);
    if (!activeKeys.has(index)) {
      audioEngine.playNote(noteName);
      setActiveKeys(prev => {
        const next = new Set(prev);
        next.add(index);
        return next;
      });
      if (onNotePlay) {
        onNotePlay(noteName);
      }
    }
  };

  const handleKeyLeave = (index: number) => {
    if (activeKeys.has(index)) {
      setActiveKeys(prev => {
        const next = new Set(prev);
        next.delete(index);
        return next;
      });
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.scrollWrapper}>
        <div className={styles.keyboard} onMouseLeave={() => setActiveKeys(new Set())}>
          {Array.from({ length: numKeys }).map((_, i) => {
            let keyClass = styles.whiteKey;
            
            const noteInOctave = i % 12;
            const isBlack = [1, 3, 6, 8, 10].includes(noteInOctave);
            
            if (isBlack) keyClass = `${styles.blackKey}`;
            
            // Check active notes status from timeline notes
            const activeMatch = timelineNotes.find(n => getMidiNoteIndex(n.note) === i);
            if (activeMatch) {
              if (activeMatch.status === 'current') {
                keyClass += ` ${styles.nextNote}`; // Next expected note gets green glowing aura
              } else if (activeMatch.status === 'correct') {
                keyClass += ` ${styles.correct}`;
              } else if (activeMatch.status === 'wrong') {
                keyClass += ` ${styles.wrong}`;
              }
            } else if (!isPlaying && i === 24 && activeHighlights.length === 0) {
              keyClass += ` ${styles.nextNote}`;
            }

            // Check highlight notes (from chord strip click)
            const highlightMatch = activeHighlights.find(note => getMidiNoteIndex(note) === i);
            if (highlightMatch) {
              keyClass += ` ${styles.active}`;
            }

            // User interaction active state
            if (activeKeys.has(i)) {
              keyClass += ` ${styles.activeUser}`;
            }
            
            // Find if this key is currently mapped to a laptop key
            const laptopKeyEntry = Object.entries(currentKeyMap).find(([_, mappedIndex]) => mappedIndex === i);
            const laptopKey = laptopKeyEntry ? laptopKeyEntry[0].toUpperCase() : null;
            const noteNameLabel = getNoteNameFromIndex(i);

            // Assign a simple finger number if it's the current active note or next expected note
            let suggestedFinger = null;
            if (activeMatch && ['current', 'wrong', 'timing-deviation'].includes(activeMatch.status)) {
               // simple heuristic based on offset from C
               const noteIdxInOctave = i % 12;
               if (noteIdxInOctave <= 2) suggestedFinger = 1;
               else if (noteIdxInOctave <= 4) suggestedFinger = 2;
               else if (noteIdxInOctave <= 6) suggestedFinger = 3;
               else if (noteIdxInOctave <= 9) suggestedFinger = 4;
               else suggestedFinger = 5;
            }

            return (
              <div 
                key={i} 
                className={keyClass}
                onMouseDown={() => handleKeyInteraction(i, 'down')}
                onMouseEnter={() => handleKeyInteraction(i, 'enter')}
                onMouseUp={() => handleKeyLeave(i)}
                onTouchStart={(e) => {
                  e.preventDefault();
                  handleKeyInteraction(i, 'down');
                }}
                onTouchEnd={(e) => {
                  e.preventDefault();
                  handleKeyLeave(i);
                }}
              >
                <div className={styles.keyLabels}>
                  {suggestedFinger && <span className={styles.fingerLabel}>👆 {suggestedFinger}</span>}
                  {laptopKey && <span className={styles.laptopKey}>{laptopKey}</span>}
                  <span className={styles.noteName}>{noteNameLabel}</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
