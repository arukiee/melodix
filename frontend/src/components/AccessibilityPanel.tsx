import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Settings, Eye, ZoomIn, Palette, Hand, ZapOff } from 'lucide-react';
import styles from './AccessibilityPanel.module.css';

interface AccessibilityPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

export function AccessibilityPanel({ isOpen, onClose }: AccessibilityPanelProps) {
  const [settings, setSettings] = useState({
    largeNotation: false,
    highContrast: false,
    colorBlind: false,
    leftHanded: false,
    reducedAnimation: false,
  });

  const toggleSetting = (key: keyof typeof settings) => {
    setSettings(prev => ({ ...prev, [key]: !prev[key] }));
    // In a real app, this would also apply CSS variables to document.documentElement
    // and save to localStorage
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <div className={styles.overlay}>
        <motion.div 
          className={styles.panel}
          initial={{ x: '100%' }}
          animate={{ x: 0 }}
          exit={{ x: '100%' }}
          transition={{ type: 'spring', damping: 25, stiffness: 200 }}
        >
          <div className={styles.header}>
            <h2 className={styles.title}><Settings size={20} /> Accessibility</h2>
            <button onClick={onClose} className={styles.closeBtn}>×</button>
          </div>
          
          <div className={styles.optionsList}>
            <div className={styles.option}>
              <div className={styles.optionInfo}>
                <ZoomIn size={18} />
                <div className={styles.optionText}>
                  <span>Larger Notation</span>
                  <small>Increase sheet music size</small>
                </div>
              </div>
              <button 
                className={`${styles.toggle} ${settings.largeNotation ? styles.on : ''}`}
                onClick={() => toggleSetting('largeNotation')}
              >
                <div className={styles.knob} />
              </button>
            </div>
            
            <div className={styles.option}>
              <div className={styles.optionInfo}>
                <Eye size={18} />
                <div className={styles.optionText}>
                  <span>High Contrast Mode</span>
                  <small>Enhance visibility of UI elements</small>
                </div>
              </div>
              <button 
                className={`${styles.toggle} ${settings.highContrast ? styles.on : ''}`}
                onClick={() => toggleSetting('highContrast')}
              >
                <div className={styles.knob} />
              </button>
            </div>
            
            <div className={styles.option}>
              <div className={styles.optionInfo}>
                <Palette size={18} />
                <div className={styles.optionText}>
                  <span>Color-Blind Friendly</span>
                  <small>Use distinct patterns for notes</small>
                </div>
              </div>
              <button 
                className={`${styles.toggle} ${settings.colorBlind ? styles.on : ''}`}
                onClick={() => toggleSetting('colorBlind')}
              >
                <div className={styles.knob} />
              </button>
            </div>
            
            <div className={styles.option}>
              <div className={styles.optionInfo}>
                <Hand size={18} />
                <div className={styles.optionText}>
                  <span>Left-Handed Mapping</span>
                  <small>Invert keyboard shortcuts</small>
                </div>
              </div>
              <button 
                className={`${styles.toggle} ${settings.leftHanded ? styles.on : ''}`}
                onClick={() => toggleSetting('leftHanded')}
              >
                <div className={styles.knob} />
              </button>
            </div>
            
            <div className={styles.option}>
              <div className={styles.optionInfo}>
                <ZapOff size={18} />
                <div className={styles.optionText}>
                  <span>Reduced Animation</span>
                  <small>Disable glowing and pulsing</small>
                </div>
              </div>
              <button 
                className={`${styles.toggle} ${settings.reducedAnimation ? styles.on : ''}`}
                onClick={() => toggleSetting('reducedAnimation')}
              >
                <div className={styles.knob} />
              </button>
            </div>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
