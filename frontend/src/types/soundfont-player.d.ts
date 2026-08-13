declare module 'soundfont-player' {
  export interface Player {
    play(note: string | number, time?: number, options?: any): void;
    stop(): void;
  }

  export function instrument(ac: AudioContext, name: string, options?: any): Promise<Player>;
}
