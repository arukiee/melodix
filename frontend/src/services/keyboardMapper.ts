import type { TimelineNote } from './timeline';

export class KeyboardMapper {
  // White keys from left to right on a standard QWERTY keyboard
  private readonly whiteKeys = ['a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', ';', "'"];
  // Black keys (accidentals) mapped to the QWERTY keys above the white keys
  // Note: 'w' is above 'a' and 's' (C#), 'e' is above 's' and 'd' (D#), etc.
  // There is no black key between E and F, or B and C.
  private readonly blackKeys = ['w', 'e', null, 't', 'y', 'u', null, 'o', 'p', null, ']'];

  private readonly noteNames = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];

  getMidiNoteIndex(midiName: string): number {
    const match = midiName.match(/^([A-G]#?)(-?\d+)$/);
    if (!match) return -1;
    const name = match[1];
    const octave = parseInt(match[2], 10);
    const index = this.noteNames.indexOf(name);
    return (octave + 1) * 12 + index - 24; // C4 (midi 60) becomes index 36.
  }

  getNoteNameFromIndex(index: number): string {
    const noteIndex = (index + 24) % 12;
    const octave = Math.floor((index + 24) / 12) - 1;
    return `${this.noteNames[noteIndex]}${octave}`;
  }

  isWhiteKey(index: number): boolean {
    const noteInOctave = (index + 24) % 12;
    // C(0), D(2), E(4), F(5), G(7), A(9), B(11) are white keys
    return [0, 2, 4, 5, 7, 9, 11].includes(noteInOctave);
  }

  /**
   * Generates a key map for the laptop keyboard based on the provided timeline notes.
   * If timeline notes are empty, it defaults to mapping starting at C4 (index 36).
   */
  generateMapping(notes: TimelineNote[]): Record<string, number> {
    const map: Record<string, number> = {};

    let minIndex = 36; // Default to C4
    
    if (notes.length > 0) {
      const indices = notes.map(n => this.getMidiNoteIndex(n.note)).filter(i => i >= 0);
      if (indices.length > 0) {
        // Find the lowest note in the piece
        let minNote = Math.min(...indices);
        // We will anchor to the lowest note directly if it's a white key, else the white key below it
        while (!this.isWhiteKey(minNote)) {
          minNote--;
        }
        minIndex = minNote;
      }
    }

    let whiteKeyIndex = 0;
    
    // Create the mapping starting from minIndex
    for (let currentNoteIdx = minIndex; currentNoteIdx < minIndex + 24; currentNoteIdx++) { // Map up to 2 octaves max if keys permit
      if (whiteKeyIndex >= this.whiteKeys.length) {
        break; // Out of laptop keys
      }
      
      if (this.isWhiteKey(currentNoteIdx)) {
        map[this.whiteKeys[whiteKeyIndex]] = currentNoteIdx;
        
        // Check if there's a black key coming next (between this and next white key)
        if (!this.isWhiteKey(currentNoteIdx + 1)) {
          const blackKeyChar = this.blackKeys[whiteKeyIndex];
          if (blackKeyChar) {
            map[blackKeyChar] = currentNoteIdx + 1;
          }
        }
        whiteKeyIndex++;
      }
    }

    return map;
  }
}

export const keyboardMapper = new KeyboardMapper();
