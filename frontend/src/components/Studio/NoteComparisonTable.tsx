import React from 'react';
import type { NoteComparisonEvent } from '../../api/practice';

interface NoteComparisonTableProps {
  notes: NoteComparisonEvent[];
  correctCount: number;
  wrongCount: number;
  missedCount: number;
  extraCount: number;
}

const resultMeta = {
  correct:  { label: '✓ Correct',  color: '#22c55e', bg: 'rgba(34,197,94,0.08)',  border: 'rgba(34,197,94,0.25)'  },
  wrong:    { label: '✗ Wrong',    color: '#ef4444', bg: 'rgba(239,68,68,0.08)',  border: 'rgba(239,68,68,0.25)'  },
  missed:   { label: '○ Missed',   color: '#f59e0b', bg: 'rgba(245,158,11,0.08)', border: 'rgba(245,158,11,0.25)' },
  extra:    { label: '+ Extra',    color: '#8b5cf6', bg: 'rgba(139,92,246,0.08)', border: 'rgba(139,92,246,0.25)' },
};

function TimingBadge({ ms }: { ms: number | null }) {
  if (ms === null) return <span style={{ color: 'var(--text-muted)' }}>—</span>;
  const abs = Math.abs(ms);
  const label = ms > 0 ? `+${abs}ms late` : ms < 0 ? `${ms}ms early` : 'on time';
  const color = abs < 60 ? '#22c55e' : abs < 150 ? '#f59e0b' : '#ef4444';
  return <span style={{ color, fontWeight: 600, fontSize: '0.8rem' }}>{label}</span>;
}

function CentsBadge({ cents }: { cents: number | null }) {
  if (cents === null) return <span style={{ color: 'var(--text-muted)' }}>—</span>;
  const abs = Math.abs(cents);
  const label = abs < 5 ? 'in tune' : cents > 0 ? `+${abs.toFixed(0)}¢ sharp` : `${cents.toFixed(0)}¢ flat`;
  const color = abs < 10 ? '#22c55e' : abs < 25 ? '#f59e0b' : '#ef4444';
  return <span style={{ color, fontSize: '0.78rem' }}>{label}</span>;
}

export function NoteComparisonTable({
  notes,
  correctCount,
  wrongCount,
  missedCount,
  extraCount,
}: NoteComparisonTableProps) {
  if (!notes || notes.length === 0) {
    return (
      <div style={{ textAlign: 'center', padding: '32px', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
        No note comparison data — make sure the lesson has expected notes configured.
      </div>
    );
  }

  const total = correctCount + wrongCount + missedCount;
  const accuracy = total > 0 ? Math.round((correctCount / total) * 100) : 0;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>

      {/* Summary bar */}
      <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
        {[
          { label: 'Correct',  count: correctCount,  color: '#22c55e' },
          { label: 'Wrong',    count: wrongCount,    color: '#ef4444' },
          { label: 'Missed',   count: missedCount,   color: '#f59e0b' },
          { label: 'Extra',    count: extraCount,    color: '#8b5cf6' },
        ].map(item => (
          <div
            key={item.label}
            style={{
              display: 'flex', alignItems: 'center', gap: '8px',
              padding: '8px 16px',
              background: 'var(--bg-card)',
              border: '1px solid var(--border-color)',
              borderRadius: '10px',
            }}
          >
            <span style={{ fontSize: '1.2rem', fontWeight: 800, color: item.color }}>{item.count}</span>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', fontWeight: 600 }}>{item.label}</span>
          </div>
        ))}

        {/* Note accuracy pill */}
        <div style={{
          marginLeft: 'auto',
          display: 'flex', alignItems: 'center', gap: '8px',
          padding: '8px 20px',
          background: accuracy >= 90 ? 'rgba(34,197,94,0.1)' : accuracy >= 70 ? 'rgba(245,158,11,0.1)' : 'rgba(239,68,68,0.1)',
          border: `1px solid ${accuracy >= 90 ? 'rgba(34,197,94,0.3)' : accuracy >= 70 ? 'rgba(245,158,11,0.3)' : 'rgba(239,68,68,0.3)'}`,
          borderRadius: '10px',
        }}>
          <span style={{
            fontSize: '1.3rem', fontWeight: 800,
            color: accuracy >= 90 ? '#22c55e' : accuracy >= 70 ? '#f59e0b' : '#ef4444',
          }}>{accuracy}%</span>
          <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', fontWeight: 600 }}>Note Accuracy</span>
        </div>
      </div>

      {/* Accuracy bar */}
      <div style={{ height: '6px', background: 'var(--bg-elevated)', borderRadius: '3px', overflow: 'hidden' }}>
        <div style={{
          height: '100%', width: `${accuracy}%`,
          background: accuracy >= 90 ? '#22c55e' : accuracy >= 70 ? '#f59e0b' : '#ef4444',
          borderRadius: '3px', transition: 'width 0.6s ease',
        }} />
      </div>

      {/* Table */}
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.84rem' }}>
          <thead>
            <tr>
              {['#', 'Expected', 'Played', 'Result', 'Timing', 'Intonation', 'Duration'].map(h => (
                <th
                  key={h}
                  style={{
                    padding: '10px 12px',
                    textAlign: 'left',
                    fontSize: '0.7rem',
                    fontWeight: 700,
                    textTransform: 'uppercase',
                    letterSpacing: '0.06em',
                    color: 'var(--text-muted)',
                    borderBottom: '1px solid var(--border-color)',
                    whiteSpace: 'nowrap',
                  }}
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {notes.map((row, i) => {
              const meta = resultMeta[row.result] ?? resultMeta.correct;
              return (
                <tr
                  key={i}
                  style={{
                    background: i % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.01)',
                    borderBottom: '1px solid rgba(255,255,255,0.04)',
                    transition: 'background 0.15s',
                  }}
                  onMouseEnter={e => (e.currentTarget.style.background = 'rgba(255,255,255,0.04)')}
                  onMouseLeave={e => (e.currentTarget.style.background = i % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.01)')}
                >
                  {/* # */}
                  <td style={{ padding: '10px 12px', color: 'var(--text-muted)', fontWeight: 600 }}>
                    {row.result !== 'extra' ? i + 1 : '—'}
                  </td>
                  {/* Expected */}
                  <td style={{ padding: '10px 12px' }}>
                    <span style={{
                      display: 'inline-block',
                      padding: '2px 8px',
                      background: 'rgba(255,255,255,0.06)',
                      borderRadius: '6px',
                      fontWeight: 700,
                      fontFamily: 'monospace',
                      fontSize: '0.9rem',
                    }}>
                      {row.expected_note}
                    </span>
                  </td>
                  {/* Played */}
                  <td style={{ padding: '10px 12px' }}>
                    <span style={{
                      display: 'inline-block',
                      padding: '2px 8px',
                      background: row.played_note ? meta.bg : 'transparent',
                      border: row.played_note ? `1px solid ${meta.border}` : 'none',
                      borderRadius: '6px',
                      fontWeight: 700,
                      fontFamily: 'monospace',
                      fontSize: '0.9rem',
                      color: row.played_note ? meta.color : 'var(--text-muted)',
                    }}>
                      {row.played_note ?? '—'}
                    </span>
                  </td>
                  {/* Result badge */}
                  <td style={{ padding: '10px 12px' }}>
                    <span style={{
                      display: 'inline-block',
                      padding: '3px 10px',
                      background: meta.bg,
                      border: `1px solid ${meta.border}`,
                      borderRadius: '20px',
                      fontSize: '0.72rem',
                      fontWeight: 700,
                      color: meta.color,
                      whiteSpace: 'nowrap',
                    }}>
                      {meta.label}
                    </span>
                  </td>
                  {/* Timing */}
                  <td style={{ padding: '10px 12px' }}>
                    <TimingBadge ms={row.timing_delta_ms} />
                  </td>
                  {/* Intonation */}
                  <td style={{ padding: '10px 12px' }}>
                    <CentsBadge cents={row.cents_off} />
                  </td>
                  {/* Duration delta */}
                  <td style={{ padding: '10px 12px' }}>
                    {row.duration_delta_ms !== null ? (
                      <span style={{
                        fontSize: '0.78rem',
                        color: Math.abs(row.duration_delta_ms) < 100 ? '#22c55e'
                          : Math.abs(row.duration_delta_ms) < 300 ? '#f59e0b'
                          : '#ef4444',
                      }}>
                        {row.duration_delta_ms > 0
                          ? `+${row.duration_delta_ms}ms`
                          : `${row.duration_delta_ms}ms`}
                      </span>
                    ) : (
                      <span style={{ color: 'var(--text-muted)' }}>—</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Reading guide */}
      <div style={{
        display: 'flex', gap: '16px', flexWrap: 'wrap',
        padding: '12px 16px',
        background: 'var(--bg-elevated)',
        borderRadius: '10px',
        fontSize: '0.72rem', color: 'var(--text-muted)',
      }}>
        <span><strong style={{ color: 'var(--text-secondary)' }}>Timing:</strong> green &lt;60ms · yellow &lt;150ms · red ≥150ms</span>
        <span><strong style={{ color: 'var(--text-secondary)' }}>Intonation:</strong> green &lt;10¢ · yellow &lt;25¢ · red ≥25¢</span>
        <span><strong style={{ color: 'var(--text-secondary)' }}>Duration:</strong> green &lt;100ms off · yellow &lt;300ms · red ≥300ms</span>
      </div>
    </div>
  );
}
