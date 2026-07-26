import { motion } from 'framer-motion';
import styles from './SheetMusic.module.css';
import { Settings, ZoomIn, ZoomOut, Search } from 'lucide-react';

export function SheetMusic() {
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
            <h1 className={styles.title}>Clair de Lune</h1>
            <h2 className={styles.composer}>Claude Debussy</h2>
          </div>

          <div className={styles.tempoMarking}>
            <span style={{ fontFamily: 'serif', fontWeight: 'bold' }}>Andante très expressif</span> (♩ = 72)
          </div>

          {/* System 1 */}
          <div className={styles.system}>
            <div className={styles.measure}>
              <div className={styles.clefs}>
                <span className={styles.treble}>𝄞</span>
                <span className={styles.bass}>𝄢</span>
              </div>
              <div className={styles.timeSig}>
                <span>9</span>
                <span>8</span>
              </div>
              <div className={styles.notesContainer}>
                {/* Mock Notes */}
                <div className={styles.staffLine} style={{ top: '20%' }} />
                <div className={styles.staffLine} style={{ top: '40%' }} />
                <div className={styles.staffLine} style={{ top: '60%' }} />
                <div className={styles.staffLine} style={{ top: '80%' }} />
                <div className={styles.staffLine} style={{ top: '100%' }} />
                
                <span className={styles.note} style={{ left: '20%', top: '30%' }}>♩</span>
                <span className={styles.note} style={{ left: '50%', top: '50%' }}>♪</span>
                <span className={styles.note} style={{ left: '80%', top: '20%' }}>♪</span>
              </div>
            </div>
            
            {/* Current measure highlight */}
            <div className={`${styles.measure} ${styles.activeMeasure}`}>
              <div className={styles.notesContainer}>
                <div className={styles.staffLine} style={{ top: '20%' }} />
                <div className={styles.staffLine} style={{ top: '40%' }} />
                <div className={styles.staffLine} style={{ top: '60%' }} />
                <div className={styles.staffLine} style={{ top: '80%' }} />
                <div className={styles.staffLine} style={{ top: '100%' }} />
                
                {/* Current note highlight */}
                <span className={`${styles.note} ${styles.activeNote}`} style={{ left: '20%', top: '40%' }}>♩</span>
                <span className={styles.note} style={{ left: '50%', top: '60%' }}>♪</span>
                <span className={styles.note} style={{ left: '80%', top: '30%' }}>♪</span>
              </div>
            </div>

            <div className={styles.measure}>
              <div className={styles.notesContainer}>
                <div className={styles.staffLine} style={{ top: '20%' }} />
                <div className={styles.staffLine} style={{ top: '40%' }} />
                <div className={styles.staffLine} style={{ top: '60%' }} />
                <div className={styles.staffLine} style={{ top: '80%' }} />
                <div className={styles.staffLine} style={{ top: '100%' }} />
                
                <span className={styles.note} style={{ left: '30%', top: '50%' }}>𝅗𝅥</span>
                <span className={styles.note} style={{ left: '70%', top: '20%' }}>♩</span>
              </div>
            </div>
          </div>

          {/* System 2 */}
          <div className={styles.system}>
            <div className={styles.measure}>
              <div className={styles.clefs}>
                <span className={styles.treble}>𝄞</span>
                <span className={styles.bass}>𝄢</span>
              </div>
              <div className={styles.notesContainer}>
                <div className={styles.staffLine} style={{ top: '20%' }} />
                <div className={styles.staffLine} style={{ top: '40%' }} />
                <div className={styles.staffLine} style={{ top: '60%' }} />
                <div className={styles.staffLine} style={{ top: '80%' }} />
                <div className={styles.staffLine} style={{ top: '100%' }} />
                
                <span className={styles.note} style={{ left: '40%', top: '40%' }}>𝅗𝅥</span>
              </div>
            </div>
            <div className={styles.measure}>
              <div className={styles.notesContainer}>
                <div className={styles.staffLine} style={{ top: '20%' }} />
                <div className={styles.staffLine} style={{ top: '40%' }} />
                <div className={styles.staffLine} style={{ top: '60%' }} />
                <div className={styles.staffLine} style={{ top: '80%' }} />
                <div className={styles.staffLine} style={{ top: '100%' }} />
                
                <span className={styles.note} style={{ left: '20%', top: '30%' }}>♩</span>
                <span className={styles.note} style={{ left: '50%', top: '70%' }}>♪</span>
                <span className={styles.note} style={{ left: '80%', top: '40%' }}>♪</span>
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
