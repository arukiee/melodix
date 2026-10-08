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
  const [playbackRate, setPlaybackRate] = useState(1.0);

  const requestRef = useRef<number | null>(null);
  const virtualTimeRef = useRef<number>(0);
  const lastFrameRef = useRef<number | null>(null);
  const playedNoteIds = useRef<Set<string>>(new Set());

  // Total duration is the end of the last note event
  const duration = events.length > 0
    ? Math.max(...events.map(e => e.relative_time + e.duration))
    : 10;

  const startPlayback = useCallback(async () => {
    if (isPlaying) return;
    await audioEngine.init();
    // Reset frame anchor so the first tick starts with 0 delta
    lastFrameRef.current = null;
    setIsPlaying(true);
  }, [isPlaying]);

  const pausePlayback = useCallback(() => {
    setIsPlaying(false);
    if (requestRef.current !== null) {
      cancelAnimationFrame(requestRef.current);
      requestRef.current = null;
    }
    lastFrameRef.current = null;
  }, []);

  const stopPlayback = useCallback(() => {
    setIsPlaying(false);
    if (requestRef.current !== null) {
      cancelAnimationFrame(requestRef.current);
      requestRef.current = null;
    }
    virtualTimeRef.current = 0;
    lastFrameRef.current = null;
    setCurrentTime(0);
    playedNoteIds.current.clear();
    setActiveNotes([]);
    setCurrentSyllableIndex(-1);
  }, []);

  const seekTo = useCallback((seconds: number) => {
    const safeSeconds = Math.max(0, Math.min(seconds, duration));
    virtualTimeRef.current = safeSeconds;
    lastFrameRef.current = null;
    setCurrentTime(safeSeconds);
    playedNoteIds.current = new Set(
      events
        .filter(e => e.relative_time < safeSeconds)
        .map(e => e.id || `${e.relative_time}-${e.note}`)
    );
  }, [duration, events]);

  // Main playback loop — integrates rate into virtual time accumulation
  useEffect(() => {
    if (!isPlaying) return;

    lastFrameRef.current = null; // reset anchor on every play/resume/rate-change

    const tick = (now: number) => {
      if (lastFrameRef.current === null) {
        lastFrameRef.current = now;
      }
      const deltaSeconds = (now - lastFrameRef.current) / 1000;
      lastFrameRef.current = now;

      // Accumulate virtual time scaled by playback rate
      virtualTimeRef.current += deltaSeconds * playbackRate;
      const elapsedSeconds = virtualTimeRef.current;

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
            audioEngine.playNote(e.note, 1.0, e.duration / playbackRate);
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
  }, [isPlaying, duration, events, autoPlayAudio, stopPlayback, playbackRate]);

  return {
    isPlaying,
    currentTime,
    duration,
    activeNotes,
    currentSyllableIndex,
    playbackRate,
    setPlaybackRate,
    startPlayback,
    pausePlayback,
    stopPlayback,
    seekTo,
  };
}