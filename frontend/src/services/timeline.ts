export interface TimelineNote {
  note: string;
  time: number;       // seconds from session start
  duration: number;   // seconds
  status: 'correct' | 'timing-deviation' | 'wrong' | 'past' | 'upcoming' | 'current';
  measureIndex: number;
}

/**
 * Builds an expected note timeline that respects BPM.
 *
 * Before Sprint 2.5: every note was hardcoded at 1.5s intervals regardless of tempo.
 * Now: beat_duration = 60 / bpm, so at 60 BPM notes are 1.0s apart,
 * at 80 BPM they are 0.75s apart, etc.
 */
export class TimelineEngine {
  private notes: TimelineNote[] = [];
  private beatDuration: number;

  constructor(songNotes: string[], bpm: number = 60) {
    // Clamp BPM to a sensible range
    const safeBpm = Math.max(20, Math.min(240, bpm));
    this.beatDuration = 60 / safeBpm;

    // Each note occupies one beat. Hold duration is 85% of beat (leaves 15% gap).
    const holdDuration = this.beatDuration * 0.85;

    this.notes = songNotes.map((note, idx) => ({
      note,
      time: idx * this.beatDuration,
      duration: holdDuration,
      status: 'upcoming' as const,
      measureIndex: Math.floor(idx / 4), // 4 beats per measure (4/4 time)
    }));
  }

  public getNotes(): TimelineNote[] {
    return [...this.notes];
  }

  public getTotalDuration(): number {
    if (this.notes.length === 0) return 0;
    const last = this.notes[this.notes.length - 1];
    return last.time + last.duration;
  }

  public getBeatDuration(): number {
    return this.beatDuration;
  }

  public getCurrentMeasureIndex(currentTime: number): number {
    const activeNote = this.notes.find(
      n => currentTime >= n.time && currentTime <= n.time + n.duration
    );
    if (activeNote) return activeNote.measureIndex;

    const pastNotes = this.notes.filter(n => currentTime > n.time);
    if (pastNotes.length > 0) return pastNotes[pastNotes.length - 1].measureIndex;
    return 0;
  }

  /**
   * Updates note statuses based on current playback position and mistakes list.
   * Mistakes are matched by comparing each mistake's timestamp to the note's
   * expected time window.
   */
  public updateState(currentTime: number, mistakes: { timestamp: number; type: string }[] = []) {
    this.notes = this.notes.map(note => {
      // Past note
      if (currentTime > note.time + note.duration) {
        const hasMistake = mistakes.some(
          m => Math.abs(m.timestamp - note.time) < this.beatDuration * 0.8
        );
        return { ...note, status: hasMistake ? 'wrong' : 'past' } as TimelineNote;
      }
      // Current note
      if (currentTime >= note.time && currentTime <= note.time + note.duration) {
        const hasTimingDeviation = mistakes.some(
          m =>
            Math.abs(m.timestamp - currentTime) < this.beatDuration * 0.5 &&
            (m.type === 'early' || m.type === 'late')
        );
        return { ...note, status: hasTimingDeviation ? 'timing-deviation' : 'current' } as TimelineNote;
      }
      // Upcoming
      return { ...note, status: 'upcoming' } as TimelineNote;
    });
  }
}
