import { motion } from 'framer-motion';
import styles from './SheetMusic.module.css';
import { Settings, ZoomIn, ZoomOut, Search } from 'lucide-react';
import type { TimelineNote } from '../../services/timeline';

export type NotationMode = 'sheet' | 'notes' | 'both' | 'chords' | 'pianoRoll';

interface SheetMusicProps {
  timelineNotes?: TimelineNote[];
  currentMeasureIndex?: number;
  notationMode?: NotationMode;
}

export function SheetMusic({ timelineNotes = [], currentMeasureIndex = 0, notationMode = 'sheet' }: SheetMusicProps) {
  // If no timeline notes provided, fallback to default labels
  const getNoteColor = (noteStatus: string) => {
    switch (noteStatus) {
      case 'correct': return '#10b981'; // Green
      case 'wrong': return '#ef4444'; // Red
      case 'timing-deviation': return '#f59e0b'; // Yellow
      case 'current': return '#3b82f6'; // Blue
      case 'past': return '#9ca3af'; // Gray
      default: return 'var(--text-primary)'; // default/white
    }
  };

  return (
    <div className={styles.container}>
      {/* Floating contextual toolbar (AI Practice Tools) */}
      <div className={styles.contextToolbar}>
        <button className={styles.toolBtn}>Slow Section</button>
        <button className={styles.toolBtn}>Explain Fingering</button>
        <button className={styles.toolBtn}>Generate Warm-up</button>
        <div className={styles.divider} />
        <button className={styles.iconBtn}><ZoomOut size={16} /></button>
        <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>100%</span>
        <button className={styles.iconBtn}><ZoomIn size={16} /></button>
      </div>

      <div className={styles.scrollArea}>
        <div className={styles.page}>
          
          <div className={styles.pageHeader}>
            <h1 className={styles.title}>Practice Song</h1>
            <h2 className={styles.composer}>Adaptive Melody</h2>
          </div>

          <div className={styles.tempoMarking}>
            <span style={{ fontFamily: 'serif', fontWeight: 'bold' }}>Andante très expressif</span>
          </div>

          {/* System 1 */}
          <div className={styles.system}>
            <div 
              className={`${styles.measure} ${currentMeasureIndex === 0 ? styles.activeMeasure : ''}`}
              style={{
                transition: 'border-color 0.2s ease, box-shadow 0.2s ease',
                border: currentMeasureIndex === 0 ? '2px solid var(--accent-primary)' : '1px solid var(--border-color)',
                boxShadow: currentMeasureIndex === 0 ? '0 0 10px rgba(59, 130, 246, 0.2)' : 'none'
              }}
            >
              <div className={styles.clefs}>
                <span className={styles.treble}>𝄞</span>
                <span className={styles.bass}>𝄢</span>
              </div>
              <div className={styles.timeSig}>
                <span>4</span>
                <span>4</span>
              </div>
              <div className={styles.notesContainer}>
                {/* Mock Notes */}
                <div className={styles.staffLine} style={{ top: '20%' }} />
                <div className={styles.staffLine} style={{ top: '40%' }} />
                <div className={styles.staffLine} style={{ top: '60%' }} />
                <div className={styles.staffLine} style={{ top: '80%' }} />
                <div className={styles.staffLine} style={{ top: '100%' }} />
                
                {/* Render dynamically formatted timeline notes if available */}
                {timelineNotes.length > 0 ? (
                  timelineNotes.slice(0, 4).map((n, idx) => {
                    const isPianoRoll = notationMode === 'pianoRoll';
                    const isChords = notationMode === 'chords';
                    
                    return (
                      <span 
                        key={idx} 
                        className={styles.note} 
                        style={{ 
                          left: `${20 + idx * 22}%`, 
                          top: isPianoRoll ? '40%' : '40%', 
                          color: getNoteColor(n.status),
                          fontWeight: n.status === 'current' ? 'bold' : 'normal',
                          fontSize: n.status === 'current' ? '1.8rem' : '1.5rem',
                          transition: 'color 0.1s ease, transform 0.1s ease',
                          ...(isPianoRoll ? {
                            display: 'inline-block',
                            width: '40px',
                            height: '16px',
                            backgroundColor: getNoteColor(n.status),
                            borderRadius: '8px',
                            opacity: n.status === 'upcoming' ? 0.4 : 1
                          } : {})
                        }}
                      >
                        {['sheet', 'both'].includes(notationMode) && '♩'}
                        {['notes', 'both'].includes(notationMode) && (
                          <span style={{ 
                            fontSize: notationMode === 'notes' ? '1.2rem' : '0.6rem', 
                            display: 'block', 
                            textAlign: 'center', 
                            marginTop: notationMode === 'notes' ? '0' : '-10px',
                            fontWeight: 'bold'
                          }}>
                            {n.note}
                          </span>
                        )}
                        {isChords && (
                          <span style={{ fontSize: '1.2rem', fontWeight: 'bold' }}>
                            {n.note.replace(/\d/, '')} Maj
                          </span>
                        )}
                      </span>
                    );
                  })
                ) : (
                  <>
                    <span className={styles.note} style={{ left: '20%', top: '30%' }}>{notationMode === 'pianoRoll' ? <div style={{width: '40px', height: '16px', backgroundColor: 'var(--text-primary)', borderRadius: '8px'}} /> : '♩'}</span>
                    <span className={styles.note} style={{ left: '50%', top: '50%' }}>{notationMode === 'pianoRoll' ? <div style={{width: '40px', height: '16px', backgroundColor: 'var(--text-primary)', borderRadius: '8px'}} /> : '♩'}</span>
                    <span className={styles.note} style={{ left: '80%', top: '20%' }}>{notationMode === 'pianoRoll' ? <div style={{width: '40px', height: '16px', backgroundColor: 'var(--text-primary)', borderRadius: '8px'}} /> : '♩'}</span>
                  </>
                )}
              </div>
            </div>
            
            <div 
              className={`${styles.measure} ${currentMeasureIndex === 1 ? styles.activeMeasure : ''}`}
              style={{
                transition: 'border-color 0.2s ease, box-shadow 0.2s ease',
                border: currentMeasureIndex === 1 ? '2px solid var(--accent-primary)' : '1px solid var(--border-color)',
                boxShadow: currentMeasureIndex === 1 ? '0 0 10px rgba(59, 130, 246, 0.2)' : 'none'
              }}
            >
              <div className={styles.notesContainer}>
                <div className={styles.staffLine} style={{ top: '20%' }} />
                <div className={styles.staffLine} style={{ top: '40%' }} />
                <div className={styles.staffLine} style={{ top: '60%' }} />
                <div className={styles.staffLine} style={{ top: '80%' }} />
                <div className={styles.staffLine} style={{ top: '100%' }} />
                
                {timelineNotes.length > 4 ? (
                  timelineNotes.slice(4, 8).map((n, idx) => {
                    const isPianoRoll = notationMode === 'pianoRoll';
                    const isChords = notationMode === 'chords';
                    
                    return (
                      <span 
                        key={idx} 
                        className={styles.note} 
                        style={{ 
                          left: `${20 + idx * 22}%`, 
                          top: '50%', 
                          color: getNoteColor(n.status),
                          fontWeight: n.status === 'current' ? 'bold' : 'normal',
                          fontSize: n.status === 'current' ? '1.8rem' : '1.5rem',
                          transition: 'color 0.1s ease, transform 0.1s ease',
                          ...(isPianoRoll ? {
                            display: 'inline-block',
                            width: '40px',
                            height: '16px',
                            backgroundColor: getNoteColor(n.status),
                            borderRadius: '8px',
                            opacity: n.status === 'upcoming' ? 0.4 : 1
                          } : {})
                        }}
                      >
                        {['sheet', 'both'].includes(notationMode) && '♩'}
                        {['notes', 'both'].includes(notationMode) && (
                          <span style={{ 
                            fontSize: notationMode === 'notes' ? '1.2rem' : '0.6rem', 
                            display: 'block', 
                            textAlign: 'center', 
                            marginTop: notationMode === 'notes' ? '0' : '-10px',
                            fontWeight: 'bold'
                          }}>
                            {n.note}
                          </span>
                        )}
                        {isChords && (
                          <span style={{ fontSize: '1.2rem', fontWeight: 'bold' }}>
                            {n.note.replace(/\d/, '')} Maj
                          </span>
                        )}
                      </span>
                    );
                  })
                ) : (
                  <>
                    <span className={styles.note} style={{ left: '20%', top: '40%' }}>{notationMode === 'pianoRoll' ? <div style={{width: '40px', height: '16px', backgroundColor: 'var(--text-primary)', borderRadius: '8px'}} /> : '♩'}</span>
                    <span className={styles.note} style={{ left: '50%', top: '60%' }}>{notationMode === 'pianoRoll' ? <div style={{width: '40px', height: '16px', backgroundColor: 'var(--text-primary)', borderRadius: '8px'}} /> : '♩'}</span>
                    <span className={styles.note} style={{ left: '80%', top: '30%' }}>{notationMode === 'pianoRoll' ? <div style={{width: '40px', height: '16px', backgroundColor: 'var(--text-primary)', borderRadius: '8px'}} /> : '♩'}</span>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
