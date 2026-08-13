import React, { useEffect, useState } from 'react';
import type { Achievement } from '../services/xpService';

interface AchievementToastProps {
  achievement: Achievement | null;
  onDismiss: () => void;
}

export function AchievementToast({ achievement, onDismiss }: AchievementToastProps) {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (achievement) {
      setVisible(true);
      const timer = setTimeout(() => {
        setVisible(false);
        setTimeout(onDismiss, 400);
      }, 3500);
      return () => clearTimeout(timer);
    }
  }, [achievement]);

  if (!achievement) return null;

  return (
    <div
      style={{
        position: 'fixed',
        top: '24px',
        left: '50%',
        transform: `translateX(-50%) translateY(${visible ? '0' : '-80px'})`,
        opacity: visible ? 1 : 0,
        zIndex: 9999,
        transition: 'transform 0.4s cubic-bezier(0.16,1,0.3,1), opacity 0.4s ease',
        pointerEvents: 'none',
      }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '16px',
          padding: '16px 24px',
          background: 'linear-gradient(135deg, #1a1a2e, #16213e)',
          border: '1px solid rgba(245,158,11,0.4)',
          borderRadius: '20px',
          boxShadow: '0 8px 32px rgba(0,0,0,0.6), 0 0 0 1px rgba(245,158,11,0.2)',
          backdropFilter: 'blur(24px)',
          minWidth: '320px',
          maxWidth: '480px',
        }}
      >
        {/* Emoji badge */}
        <div
          style={{
            width: '52px',
            height: '52px',
            borderRadius: '50%',
            background: 'rgba(245,158,11,0.15)',
            border: '2px solid rgba(245,158,11,0.4)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '1.6rem',
            flexShrink: 0,
            animation: 'achievementBounce 0.6s cubic-bezier(0.36,0.07,0.19,0.97) both',
          }}
        >
          {achievement.emoji}
        </div>

        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontSize: '0.72rem', fontWeight: 700, color: '#f59e0b', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '2px' }}>
            🏆 Achievement Unlocked!
          </div>
          <div style={{ fontSize: '1rem', fontWeight: 700, color: '#fff', marginBottom: '2px' }}>
            {achievement.title}
          </div>
          <div style={{ fontSize: '0.8rem', color: 'rgba(255,255,255,0.6)', lineHeight: 1.4 }}>
            {achievement.description}
          </div>
        </div>

        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            flexShrink: 0,
          }}
        >
          <span style={{ fontSize: '1rem', fontWeight: 800, color: '#f59e0b' }}>+{achievement.xpReward}</span>
          <span style={{ fontSize: '0.65rem', color: 'rgba(245,158,11,0.7)', fontWeight: 600 }}>XP</span>
        </div>
      </div>

      <style>{`
        @keyframes achievementBounce {
          0%   { transform: scale(0.3) rotate(-10deg); opacity: 0; }
          50%  { transform: scale(1.1) rotate(3deg); opacity: 1; }
          70%  { transform: scale(0.95) rotate(-2deg); }
          100% { transform: scale(1) rotate(0deg); opacity: 1; }
        }
      `}</style>
    </div>
  );
}
