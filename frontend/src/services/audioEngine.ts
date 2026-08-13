import * as Tone from 'tone';
import Soundfont from 'soundfont-player';

class AudioEngine {
  private ac: AudioContext | null = null;
  private piano: Soundfont.Player | null = null;
  private initialized: boolean = false;

  async init() {
    if (this.initialized) return;
    
    // Tone.start() must be called after a user interaction
    await Tone.start();
    
    // Use Tone's context
    this.ac = Tone.getContext().rawContext as AudioContext;
    
    // Load piano soundfont
    // We'll use the default Gleitz soundfont for now, can be configured for local salamander later.
    this.piano = await Soundfont.instrument(this.ac, 'acoustic_grand_piano');
    
    this.initialized = true;
  }

  playNote(note: string, velocity: number = 1.0, duration: number = 0.5) {
    if (!this.piano) return;
    this.piano.play(note, this.ac?.currentTime, {
      gain: velocity,
      duration: duration
    });
  }

  playChord(notes: string[], velocity: number = 1.0, duration: number = 0.5) {
    if (!this.piano) return;
    const now = this.ac?.currentTime || 0;
    notes.forEach(note => {
      this.piano!.play(note, now, {
        gain: velocity,
        duration: duration
      });
    });
  }

  isInitialized() {
    return this.initialized;
  }
}

export const audioEngine = new AudioEngine();
