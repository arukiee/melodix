import { useState, useEffect, useRef, useCallback } from 'react';
import type { ExpectedEvent } from '../api/practice';
import { audioEngine } from './audioEngine';

export interface PlaybackState {
  isPlaying: boolean;
  currentTime: number;
  activeNotes: string[];
  currentSyllableIndex: number;
}

export function usePlaybackController(
  events: ExpectedEvent[],
  bpm: number = 60,
  autoPlayAudio: boolean = false
) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [activeNotes, setActiveNotes] = useState<string[]>([]);
  const [currentSyllableIndex, setCurrentSyllableIndex] = useState(-1);

  const requestRef = useRef<number | null>(null);
  const startTimeRef = useRef<number | null>(null);
  const pauseTimeRef = useRef<number>(0);
  const playedNoteIds = useRef<Set<string>>(new Set());

  // Total duration is the end of the last note event
  const duration = events.length > 0 
    ? Math.max(...events.map(e => e.relative_time + e.duration))
    : 10;

  const startPlayback = useCallback(async () => {
    if (isPlaying) return;
    
    // Ensure sound font / audio context is initialized
    await audioEngine.init();

    setIsPlaying(true);
    startTimeRef.current = performance.now() - (pauseTimeRef.current * 1000);
  }, [isPlaying]);

  const pausePlayback = useCallback(() => {
    setIsPlaying(false);
    if (requestRef.current !== null) {
      cancelAnimationFrame(requestRef.current);
      requestRef.current = null;
    }
    pauseTimeRef.current = currentTime;
  }, [currentTime]);

  const stopPlayback = useCallback(() => {
    setIsPlaying(false);
    if (requestRef.current !== null) {
      cancelAnimationFrame(requestRef.current);
      requestRef.current = null;
    }
    setCurrentTime(0);
    pauseTimeRef.current = 0;
    playedNoteIds.current.clear();
    setActiveNotes([]);
    setCurrentSyllableIndex(-1);
  }, []);

  const seekTo = useCallback((seconds: number) => {
    const safeSeconds = Math.max(0, Math.min(seconds, duration));
    setCurrentTime(safeSeconds);
    pauseTimeRef.current = safeSeconds;
    if (isPlaying) {
      startTimeRef.current = performance.now() - (safeSeconds * 1000);
    }
    // Clear future played notes status
    playedNoteIds.current = new Set(
      events
        .filter(e => e.relative_time < safeSeconds)
        .map(e => e.id || `${e.relative_time}-${e.note}`)
    );
  }, [isPlaying, duration, events]);

  // Main playback loop
  useEffect(() => {
    if (!isPlaying) return;

    const tick = (now: number) => {
      if (startTimeRef.current === null) return;
      const elapsedSeconds = (now - startTimeRef.current) / 1000;

      if (elapsedSeconds >= duration) {
        stopPlayback();
        return;
      }

      setCurrentTime(elapsedSeconds);

      // 1. Identify currently active notes (notes held at this timestamp)
      const active: string[] = [];
      events.forEach(e => {
        if (elapsedSeconds >= e.relative_time && elapsedSeconds <= (e.relative_time + e.duration)) {
          active.push(e.note);
        }
      });
      setActiveNotes(active);

      // 2. Play audio for newly crossed notes (if autoPlayAudio is enabled)
      if (autoPlayAudio) {
        events.forEach(e => {
          const uniqueId = e.id || `${e.relative_time}-${e.note}`;
          if (elapsedSeconds >= e.relative_time && !playedNoteIds.current.has(uniqueId)) {
            playedNoteIds.current.add(uniqueId);
            audioEngine.playNote(e.note, 1.0, e.duration);
          }
        });
      }

      // 3. Update active lyric syllable matching the time
      let syllableIdx = -1;
      for (let i = 0; i < events.length; i++) {
        if (elapsedSeconds >= events[i].relative_time) {
          syllableIdx = i;
        }
      }
      setCurrentSyllableIndex(syllableIdx);

      requestRef.current = requestAnimationFrame(tick);
    };

    requestRef.current = requestAnimationFrame(tick);

    return () => {
      if (requestRef.current !== null) {
        cancelAnimationFrame(requestRef.current);
      }
    };
  }, [isPlaying, duration, events, autoPlayAudio, stopPlayback]);

  return {
    isPlaying,
    currentTime,
    duration,
    activeNotes,
    currentSyllableIndex,
    startPlayback,
    pausePlayback,
    stopPlayback,
    seekTo,
  };
}
