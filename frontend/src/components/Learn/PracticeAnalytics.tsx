import React from 'react';
import { BarChart3, Clock, Flame, Star, Target, TrendingUp, Award } from 'lucide-react';
import { xpService } from '../../services/xpService';

export const PracticeAnalytics: React.FC = () => {
  const sessions = xpService.getRecentSessions(10);
  const totalXP = xpService.getTotalXP();
  const streak = xpService.getStreak();
  const level = xpService.getLevel();
  const levelTitle = xpService.getLevelTitle();
  const { current: levelXP, needed: levelNeeded } = xpService.getProgressToNextLevel();
  const totalMinutes = xpService.getTotalPracticeMinutes();
  const unlockedAchievements = xpService.getUnlockedAchievements();

  const avgScore = sessions.length > 0
    ? Math.round(sessions.reduce((a, s) => a + s.score, 0) / sessions.length)
    : 0;

  const last7Days = Array.from({ length: 7 }).map((_, i) => {
    const d = new Date(Date.now() - (6 - i) * 86400000).toDateString();
    const daySessions = sessions.filter(s => new Date(s.date).toDateString() === d);
    return {
      day: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'][new Date(Date.now() - (6 - i) * 86400000).getDay()],
      count: daySessions.length,
      avgScore: daySessions.length ? Math.round(daySessions.reduce((a, s) => a + s.score, 0) / daySessions.length) : 0,
    };
  });

  const maxScore = Math.max(...last7Days.map(d => d.avgScore), 1);

  if (sessions.length === 0) {
    return (
      <div style={{ textAlign: 'center', padding: '80px 0', color: 'var(--text-secondary)' }}>
        <BarChart3 size={48} color="var(--text-muted)" style={{ margin: '0 auto 16px' }} />
        <h3 style={{ fontSize: '1.2rem', marginBottom: '8px' }}>No practice data yet</h3>
        <p style={{ maxWidth: '360px', margin: '0 auto', fontSize: '0.9rem', color: 'var(--text-muted)' }}>
          Complete your first lesson step on the Piano Journey to start tracking your progress.
        </p>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>

      {/* Stat cards row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))', gap: '16px' }}>
        {[
          { icon: <Star size={20} color="#f59e0b" />, label: 'Total XP', value: totalXP.toLocaleString(), color: '#f59e0b' },
          { icon: <Flame size={20} color="#ef4444" />, label: 'Day Streak', value: `${streak} days`, color: '#ef4444' },
          { icon: <Target size={20} color="#22c55e" />, label: 'Avg Score', value: `${avgScore}%`, color: '#22c55e' },
          { icon: <Clock size={20} color="#3b82f6" />, label: 'Practice Time', value: `${totalMinutes} min`, color: '#3b82f6' },
          { icon: <TrendingUp size={20} color="#a855f7" />, label: 'Sessions', value: sessions.length.toString(), color: '#a855f7' },
        ].map(stat => (
          <div
            key={stat.label}
            style={{
              padding: '20px',
              background: 'var(--bg-card)',
              border: '1px solid var(--border-color)',
              borderRadius: '16px',
              display: 'flex',
              flexDirection: 'column',
              gap: '10px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              {stat.icon}
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600 }}>{stat.label}</span>
            </div>
            <span style={{ fontSize: '1.5rem', fontWeight: 800, color: stat.color, letterSpacing: '-0.02em' }}>{stat.value}</span>
          </div>
        ))}
      </div>

      {/* Level progress */}
      <div style={{ padding: '20px', background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: '16px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
              Current Level
            </div>
            <div style={{ fontSize: '1.1rem', fontWeight: 700 }}>Level {level} — {levelTitle}</div>
          </div>
          <span style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>{levelXP} / {levelNeeded} XP</span>
        </div>
        <div style={{ height: '8px', background: 'var(--bg-elevated)', borderRadius: '4px', overflow: 'hidden' }}>
          <div style={{
            height: '100%',
            width: `${Math.min(100, Math.round((levelXP / levelNeeded) * 100))}%`,
            background: 'linear-gradient(90deg, #a855f7, #3b82f6)',
            borderRadius: '4px',
            transition: 'width 0.6s ease',
          }} />
        </div>
      </div>

      {/* 7-day bar chart */}
      <div style={{ padding: '20px', background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: '16px' }}>
        <h3 style={{ fontSize: '0.95rem', fontWeight: 700, marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <BarChart3 size={18} color="var(--text-secondary)" />
          Score — Last 7 Days
        </h3>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'flex-end', height: '100px' }}>
          {last7Days.map((d, i) => (
            <div key={i} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '6px' }}>
              <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)', fontWeight: 600 }}>
                {d.avgScore > 0 ? `${d.avgScore}%` : ''}
              </span>
              <div style={{ width: '100%', display: 'flex', alignItems: 'flex-end', height: '70px' }}>
                <div
                  style={{
                    width: '100%',
                    height: d.avgScore > 0 ? `${Math.round((d.avgScore / maxScore) * 100)}%` : '4px',
                    background: d.avgScore >= 90 ? '#22c55e' : d.avgScore >= 70 ? '#3b82f6' : d.avgScore > 0 ? '#f59e0b' : 'var(--bg-elevated)',
                    borderRadius: '6px 6px 3px 3px',
                    transition: 'height 0.5s ease',
                    minHeight: '4px',
                  }}
                />
              </div>
              <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>{d.day}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Recent sessions */}
      <div style={{ padding: '20px', background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: '16px' }}>
        <h3 style={{ fontSize: '0.95rem', fontWeight: 700, marginBottom: '16px' }}>Recent Sessions</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {sessions.slice(0, 5).map(s => (
            <div key={s.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 0', borderBottom: '1px solid var(--border-color)' }}>
              <div>
                <div style={{ fontSize: '0.9rem', fontWeight: 600 }}>{s.songTitle}</div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  {new Date(s.date).toLocaleDateString()} · {s.bpm} BPM · {Math.round(s.durationSeconds / 60)}m
                </div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '1.1rem', fontWeight: 800, color: s.score >= 90 ? '#22c55e' : s.score >= 70 ? '#f59e0b' : '#ef4444' }}>
                  {s.score}%
                </div>
                <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>
                  P:{s.pitchScore}% R:{s.rhythmScore}%
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Achievements */}
      {unlockedAchievements.length > 0 && (
        <div style={{ padding: '20px', background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: '16px' }}>
          <h3 style={{ fontSize: '0.95rem', fontWeight: 700, marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Award size={18} color="#f59e0b" /> Badges Earned ({unlockedAchievements.length})
          </h3>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px' }}>
            {unlockedAchievements.map(a => (
              <div
                key={a.id}
                title={`${a.title}: ${a.description}`}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '8px 14px',
                  background: 'rgba(245,158,11,0.08)',
                  border: '1px solid rgba(245,158,11,0.2)',
                  borderRadius: '12px',
                  fontSize: '0.8rem',
                  fontWeight: 600,
                  cursor: 'default',
                }}
              >
                <span style={{ fontSize: '1rem' }}>{a.emoji}</span>
                <span style={{ color: 'var(--text-secondary)' }}>{a.title}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
