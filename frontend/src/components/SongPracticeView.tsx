import React from 'react';
import { Play, CheckCircle, Lock, PlayCircle, Award, Volume2, Info } from 'lucide-react';
import type { PracticeMission, PracticePhase } from '../api/practice';

interface SongPracticeViewProps {
  songTitle: string;
  songDescription?: string;
  phases: PracticePhase[];
  onBack: () => void;
  onSelectMission: (mission: PracticeMission) => void;
}

export const SongPracticeView: React.FC<SongPracticeViewProps> = ({
  songTitle,
  songDescription,
  phases,
  onBack,
  onSelectMission,
}) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return '#10b981'; // green
      case 'in_progress':
        return '#f59e0b'; // orange/yellow
      case 'available':
        return '#3b82f6'; // blue
      default:
        return '#6b7280'; // gray (locked)
    }
  };

  const getMissionIcon = (type: string, status: string) => {
    if (status === 'locked') return <Lock size={20} color="var(--text-muted)" />;
    if (status === 'completed') return <CheckCircle size={20} color="#10b981" />;

    switch (type) {
      case 'listen':
        return <Volume2 size={20} color="var(--accent-primary)" />;
      case 'right_hand':
      case 'left_hand':
      case 'both_hands':
        return <PlayCircle size={20} color="var(--accent-primary)" />;
      case 'tempo':
        return <Play size={20} color="var(--accent-primary)" />;
      case 'performance':
        return <Award size={20} color="var(--accent-primary)" />;
      default:
        return <Info size={20} color="var(--accent-primary)" />;
    }
  };

  // Compute total progress
  const allMissions = phases.flatMap(p => p.missions);
  const completedMissions = allMissions.filter(m => m.status === 'completed').length;
  const totalMissions = allMissions.length;
  const percentage = totalMissions > 0 ? Math.round((completedMissions / totalMissions) * 100) : 0;

  return (
    <div style={{ padding: '24px 0' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '24px' }}>
        <div>
          <h2 style={{ fontSize: '2rem', fontWeight: 'bold', margin: '0 0 8px 0' }}>{songTitle}</h2>
          {songDescription && <p style={{ color: 'var(--text-secondary)', margin: '0 0 16px 0' }}>{songDescription}</p>}
        </div>
        <button
          onClick={onBack}
          style={{
            padding: '8px 16px',
            backgroundColor: 'var(--bg-card)',
            border: '1px solid var(--border-color)',
            color: 'var(--text-primary)',
            borderRadius: 'var(--radius-button)',
            cursor: 'pointer',
            fontWeight: '600',
            transition: 'all 0.2s',
          }}
          onMouseEnter={(e) => (e.currentTarget.style.borderColor = 'var(--accent-primary)')}
          onMouseLeave={(e) => (e.currentTarget.style.borderColor = 'var(--border-color)')}
        >
          Back to Path
        </button>
      </div>

      {/* General Progress Bar */}
      <div
        style={{
          padding: '20px',
          backgroundColor: 'var(--bg-card)',
          borderRadius: 'var(--radius-card)',
          border: '1px solid var(--border-color)',
          marginBottom: '32px',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', fontSize: '0.95rem' }}>
          <span style={{ fontWeight: '600' }}>Overall Song Progress</span>
          <span style={{ color: 'var(--text-secondary)' }}>{completedMissions} of {totalMissions} missions completed ({percentage}%)</span>
        </div>
        <div style={{ width: '100%', height: '8px', backgroundColor: 'var(--border-color)', borderRadius: '4px', overflow: 'hidden' }}>
          <div
            style={{
              width: `${percentage}%`,
              height: '100%',
              backgroundColor: '#10b981',
              transition: 'width 0.4s ease-out',
            }}
          ></div>
        </div>
      </div>

      {/* Phases and Missions List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
        {phases.map((phase) => (
          <div key={phase.id}>
            <h3
              style={{
                fontSize: '1.25rem',
                fontWeight: '700',
                marginBottom: '16px',
                borderBottom: '1px solid var(--border-color)',
                paddingBottom: '8px',
                color: 'var(--text-primary)',
              }}
            >
              {phase.title}
            </h3>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {phase.missions.map((mission) => {
                const isLocked = mission.status === 'locked';
                const statusColor = getStatusColor(mission.status);

                return (
                  <div
                    key={mission.id}
                    onClick={() => {
                      if (!isLocked) onSelectMission(mission);
                    }}
                    style={{
                      padding: '16px 20px',
                      backgroundColor: 'var(--bg-card)',
                      borderRadius: 'var(--radius-card)',
                      border: '1px solid var(--border-color)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      cursor: isLocked ? 'not-allowed' : 'pointer',
                      opacity: isLocked ? 0.6 : 1,
                      transition: 'all 0.2s',
                    }}
                    onMouseEnter={(e) => {
                      if (!isLocked) {
                        e.currentTarget.style.borderColor = 'var(--accent-primary)';
                        e.currentTarget.style.transform = 'translateX(4px)';
                      }
                    }}
                    onMouseLeave={(e) => {
                      if (!isLocked) {
                        e.currentTarget.style.borderColor = 'var(--border-color)';
                        e.currentTarget.style.transform = 'none';
                      }
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                      <div>{getMissionIcon(mission.type, mission.status)}</div>
                      <div>
                        <h4
                          style={{
                            margin: '0 0 4px 0',
                            fontSize: '1.05rem',
                            fontWeight: '600',
                            color: isLocked ? 'var(--text-muted)' : 'var(--text-primary)',
                          }}
                        >
                          {mission.title}
                          {mission.bpm && (
                            <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginLeft: '8px' }}>
                              ({mission.bpm} BPM)
                            </span>
                          )}
                        </h4>
                        {mission.learningGoal && (
                          <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                            {mission.learningGoal}
                          </p>
                        )}
                      </div>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                      {mission.xpReward && !isLocked && (
                        <span style={{ fontSize: '0.85rem', color: '#f59e0b', fontWeight: '600' }}>
                          +{mission.xpReward} XP
                        </span>
                      )}
                      <span
                        style={{
                          fontSize: '0.8rem',
                          fontWeight: '700',
                          padding: '4px 8px',
                          borderRadius: '4px',
                          backgroundColor: `${statusColor}22`,
                          color: statusColor,
                          textTransform: 'uppercase',
                        }}
                      >
                        {mission.status.replace('_', ' ')}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
