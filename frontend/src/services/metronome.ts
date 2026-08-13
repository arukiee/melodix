export class MetronomeService {
  private audioCtx: AudioContext | null = null;
  private isRunning: boolean = false;
  private bpm: number = 60;
  private nextNoteTime: number = 0.0;
  private currentBeat: number = 0;
  private timerId: any = null;
  
  private lookahead: number = 25.0; // How often to call scheduler (ms)
  private scheduleAheadTime: number = 0.1; // How far ahead to schedule audio (s)
  
  private onBeatCallback: ((beat: number) => void) | null = null;

  constructor(onBeat?: (beat: number) => void) {
    if (onBeat) {
      this.onBeatCallback = onBeat;
    }
  }

  public setBpm(newBpm: number) {
    this.bpm = Math.max(30, Math.min(240, newBpm));
  }

  public getBpm(): number {
    return this.bpm;
  }

  public start(bpm: number) {
    if (this.isRunning) return;
    
    this.bpm = bpm;
    const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
    this.audioCtx = new AudioContextClass();
    this.isRunning = true;
    this.currentBeat = 0;
    this.nextNoteTime = this.audioCtx.currentTime + 0.05;
    
    this.scheduler();
  }

  public stop() {
    if (!this.isRunning) return;
    
    this.isRunning = false;
    if (this.timerId) {
      clearTimeout(this.timerId);
    }
    if (this.audioCtx && this.audioCtx.state !== 'closed') {
      this.audioCtx.close();
    }
    this.audioCtx = null;
  }

  private scheduler() {
    if (!this.isRunning || !this.audioCtx) return;

    while (this.nextNoteTime < this.audioCtx.currentTime + this.scheduleAheadTime) {
      this.scheduleNote(this.currentBeat, this.nextNoteTime);
      this.advanceNote();
    }
    
    this.timerId = setTimeout(() => this.scheduler(), this.lookahead);
  }

  private advanceNote() {
    const secondsPerBeat = 60.0 / this.bpm;
    this.nextNoteTime += secondsPerBeat;
    this.currentBeat = (this.currentBeat + 1) % 4; // 4/4 signature
  }

  private scheduleNote(beat: number, time: number) {
    if (!this.audioCtx) return;

    const osc = this.audioCtx.createOscillator();
    const gainNode = this.audioCtx.createGain();
    
    osc.connect(gainNode);
    gainNode.connect(this.audioCtx.destination);
    
    // Accent on first beat
    if (beat === 0) {
      osc.frequency.setValueAtTime(1000, time); // High pitched woodblock accent
      gainNode.gain.setValueAtTime(0.6, time);
    } else {
      osc.frequency.setValueAtTime(600, time); // Lower wooden beep
      gainNode.gain.setValueAtTime(0.3, time);
    }

    gainNode.gain.exponentialRampToValueAtTime(0.001, time + 0.08);
    
    osc.start(time);
    osc.stop(time + 0.1);

    // Call UI trigger
    if (this.onBeatCallback) {
      const delay = (time - this.audioCtx.currentTime) * 1000;
      setTimeout(() => {
        if (this.isRunning && this.onBeatCallback) {
          this.onBeatCallback(beat + 1);
        }
      }, Math.max(0, delay));
    }
  }
}
