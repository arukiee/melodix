import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Play, Info, CheckCircle, Circle } from 'lucide-react';
import type { PracticeMission } from '../../api/practice';
import type { AdaptiveEngineState } from '../../services/adaptiveEngine';

interface LessonPreviewProps {
  isOpen: boolean;
  mission: PracticeMission;
  engineState: AdaptiveEngineState | null;
  onStart: () => void;
  onClose: () => void;
}

export function LessonPreview({ isOpen, mission, engineState, onStart, onClose }: LessonPreviewProps) {
  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <div style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.7)',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        zIndex: 2000,
        backdropFilter: 'blur(4px)'
      }}>
        <motion.div 
          initial={{ scale: 0.9, opacity: 0, y: 20 }}
          animate={{ scale: 1, opacity: 1, y: 0 }}
          exit={{ scale: 0.9, opacity: 0, y: 20 }}
          style={{
            backgroundColor: 'var(--bg-card)',
            border: '1px solid var(--border-color)',
            borderRadius: 'var(--radius-card)',
            padding: '32px',
            width: '90%',
            maxWidth: '500px',
            boxShadow: '0 20px 40px rgba(0, 0, 0, 0.4)',
            position: 'relative',
            maxHeight: '90vh',
            overflowY: 'auto'
          }}
        >
          <button 
            onClick={onClose}
            style={{
              position: 'absolute',
              top: '16px',
              right: '16px',
              background: 'none',
              border: 'none',
              color: 'var(--text-muted)',
              cursor: 'pointer',
              fontSize: '1.2rem'
            }}
          >
            ×
          </button>
          
          <h2 style={{ margin: '0 0 8px 0', fontSize: '1.8rem', fontWeight: 800 }}>{mission.title}</h2>
          <p style={{ margin: '0 0 24px 0', color: 'var(--text-secondary)' }}>
            {engineState?.activeSection?.title ? `Current Section: ${engineState.activeSection.title}` : "Adaptive Learning Engine"}
          </p>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', marginBottom: '32px' }}>
            <h4 style={{ margin: 0, color: 'var(--text-primary)' }}>Your Learning Journey</h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {engineState ? (
                <div style={{ padding: '16px', background: 'var(--bg-secondary)', borderRadius: '8px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
                    <div style={{ width: '32px', height: '32px', borderRadius: '50%', backgroundColor: 'var(--accent-primary)', color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold' }}>
                      {engineState.currentStageIndex + 1}
                    </div>
                    <div>
                      <div style={{ fontWeight: 'bold' }}>{engineState.activeStage?.name || "Next Stage"}</div>
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                        Target Tempo: {engineState.currentBpm} BPM ({engineState.activeStage?.tempo_pct}% speed)
                      </div>
                    </div>
                  </div>
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Info size={14} /> 
                    {engineState.activeStage?.type === 'listen' ? "Listen to the melody without playing." : 
                     engineState.activeStage?.type === 'watch' ? "Watch the correct notes highlight." : 
                     "Play the highlighted notes."}
                  </div>
                </div>
              ) : (
                <>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px', opacity: 0.5 }}>
                    <CheckCircle size={20} color="#10b981" />
                    <span>1. Listen & Watch</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <Circle size={20} color="var(--accent-primary)" />
                    <span style={{ fontWeight: 'bold' }}>2. Single Notes</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px', opacity: 0.5 }}>
                    <Circle size={20} color="var(--border-color)" />
                    <span>3. Right Hand (Slow)</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px', opacity: 0.5 }}>
                    <Circle size={20} color="var(--border-color)" />
                    <span>4. Left Hand (Slow)</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px', opacity: 0.5 }}>
                    <Circle size={20} color="var(--border-color)" />
                    <span>...</span>
                  </div>
                </>
              )}
            </div>
          </div>
          
          <button 
            onClick={onStart}
            style={{
              width: '100%',
              padding: '16px',
              backgroundColor: 'var(--accent-primary)',
              color: 'white',
              border: 'none',
              borderRadius: 'var(--radius-button)',
              fontSize: '1.1rem',
              fontWeight: 700,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '12px',
              transition: 'all 0.2s ease',
            }}
            onMouseOver={(e) => e.currentTarget.style.transform = 'translateY(-2px)'}
            onMouseOut={(e) => e.currentTarget.style.transform = 'translateY(0)'}
          >
            <Play size={20} fill="currentColor" />
            Start Practice
          </button>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
