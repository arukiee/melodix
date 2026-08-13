import { PitchDetector } from 'pitchy';

export type NoteDetectionCallback = (note: string, pitch: number, clarity: number) => void;

class LiveNoteDetector {
  private audioContext: AudioContext | null = null;
  private analyser: AnalyserNode | null = null;
  private stream: MediaStream | null = null;
  private detector: PitchDetector<Float32Array> | null = null;
  private inputBuffer: Float32Array | null = null;
  private animationFrameId: number | null = null;
  private callbacks: Set<NoteDetectionCallback> = new Set();
  
  private isListening = false;

  subscribe(cb: NoteDetectionCallback) {
    this.callbacks.add(cb);
    return () => this.callbacks.delete(cb);
  }

  async startListening() {
    if (this.isListening) return;

    try {
      this.stream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
      this.audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
      this.analyser = this.audioContext.createAnalyser();
      this.analyser.fftSize = 2048;
      
      const source = this.audioContext.createMediaStreamSource(this.stream);
      source.connect(this.analyser);

      this.detector = PitchDetector.forFloat32Array(this.analyser.fftSize);
      this.inputBuffer = new Float32Array(this.detector.inputLength);

      this.isListening = true;
      this.detectPitch();
    } catch (err) {
      console.error("Error accessing microphone for pitch detection:", err);
    }
  }

  stopListening() {
    if (!this.isListening) return;

    if (this.animationFrameId !== null) {
      cancelAnimationFrame(this.animationFrameId);
      this.animationFrameId = null;
    }

    if (this.stream) {
      this.stream.getTracks().forEach(track => track.stop());
      this.stream = null;
    }

    if (this.audioContext && this.audioContext.state !== 'closed') {
      this.audioContext.close();
      this.audioContext = null;
    }

    this.isListening = false;
  }

  private detectPitch = () => {
    if (!this.isListening || !this.analyser || !this.detector || !this.inputBuffer || !this.audioContext) return;

    this.analyser.getFloatTimeDomainData(this.inputBuffer);
    
    // Calculate volume to avoid triggering on background noise
    let sum = 0;
    for (let i = 0; i < this.inputBuffer.length; i++) {
        sum += this.inputBuffer[i] * this.inputBuffer[i];
    }
    const rms = Math.sqrt(sum / this.inputBuffer.length);
    
    if (rms > 0.01) { // Threshold for volume
      const [pitch, clarity] = this.detector.findPitch(this.inputBuffer, this.audioContext.sampleRate);
      
      if (clarity > 0.8) {
        const noteName = this.pitchToNoteName(pitch);
        this.callbacks.forEach(cb => cb(noteName, pitch, clarity));
      }
    }

    this.animationFrameId = requestAnimationFrame(this.detectPitch);
  }

  private pitchToNoteName(pitch: number): string {
    const noteNames = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];
    // A4 = 440 Hz
    // Pitch equation: P = 69 + 12 * log2(f / 440)
    const midiNum = Math.round(69 + 12 * Math.log2(pitch / 440));
    const octave = Math.floor(midiNum / 12) - 1;
    const noteIndex = midiNum % 12;
    return `${noteNames[noteIndex]}${octave}`;
  }
}

export const liveNoteDetector = new LiveNoteDetector();
