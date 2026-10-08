import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import type {
  PracticeMission, PracticePhase,
  LearningLevel, LyricAlignment, SongPhrase,
  PracticeSessionResponse,
} from '../api/practice';
import { getPipelineStatus, getSongById } from '../api/audio';
import { LearnModeWorkspace }    from '../components/Studio/LearnModeWorkspace';
import { PracticeModeWorkspace } from '../components/Studio/PracticeModeWorkspace';
import { PerformModeWorkspace }  from '../components/Studio/PerformModeWorkspace';
import { practiceApi }           from '../api/practice';
import styles from './Studio.module.css';

// ── Mode tab type ──────────────────────────────────────────────────────────
type GlobalMode = 'learn' | 'practice' | 'perform';

const MODE_META: Record<GlobalMode, { label: string; emoji: string; color: string }> = {
  learn:   { label: 'Learn',   emoji: '🟢', color: '#22c55e' },
  practice:{ label: 'Practice',emoji: '🔵', color: '#3b82f6' },
  perform: { label: 'Perform', emoji: '🟣', color: '#a855f7' },
};

// ── Level-to-mode mapping ──────────────────────────────────────────────────
function levelToMode(levelNumber: number): GlobalMode {
  if (levelNumber <= 2) return 'learn';
  if (levelNumber <= 4) return 'practice';
  return 'perform';
}

export function Studio() {
  const navigate  = useNavigate();
  const { songId: routeId } = useParams<{ songId: string }>();

  // Raw API data
  const [curriculum,     setCurriculum]     = useState<PracticeSessionResponse | null>(null);
  const [songTitle,      setSongTitle]      = useState('AI Curriculum Practice');
  const [isJobMode,      setIsJobMode]      = useState(false);
  const [isLoading,      setIsLoading]      = useState(true);
  const [error,          setError]          = useState<string | null>(null);

  // UI state
  const [globalMode,     setGlobalMode]     = useState<GlobalMode>('learn');
  const [activeMission,  setActiveMission]  = useState<PracticeMission | null>(null);
  const [activeLevel,    setActiveLevel]    = useState<LearningLevel | null>(null);
  const [sidebarOpen,    setSidebarOpen]    = useState(true);

  // Derived
  const levels:         LearningLevel[]  = curriculum?.levels  ?? [];
  const lyricAlignment: LyricAlignment | null = curriculum?.lyricAlignment ?? null;
  const phrases:        SongPhrase[]     = curriculum?.phrases  ?? [];
  const legacyPhases:   PracticePhase[]  = curriculum?.phases   ?? [];

  // Filter levels by current global mode
  const visibleLevels = levels.filter(lv => lv.learningMode === globalMode);

  useEffect(() => {
    const fetchCurriculum = async () => {
      if (!routeId) { setError("No song ID found."); setIsLoading(false); return; }
      try {
        setIsLoading(true);
        let curr: PracticeSessionResponse;
        let isJob = false;

        // 1. Try loading as a catalog song
        try {
          curr = await practiceApi.getSongPractice(routeId);
          isJob = false;
        } catch {
          // 2. Fallback to processing job for uploaded audio files
          curr = await practiceApi.getJobPractice(routeId);
          isJob = true;
        }

        setIsJobMode(isJob);
        setCurriculum(curr);

        // Resume the persisted mission cursor when the learner reopens a song.
        const resumed = (curr.levels ?? []).flatMap(level =>
          level.missions.map(mission => ({ level, mission }))
        ).find(({ mission }) => mission.id === curr.current_mission_id);
        const firstLevel = (curr.levels ?? [])[0];
        if (resumed) {
          setActiveMission(resumed.mission);
          setActiveLevel(resumed.level);
          setGlobalMode(levelToMode(resumed.level.levelNumber));
        } else if (firstLevel?.missions?.[0]) {
          setActiveMission(firstLevel.missions[0]);
          setActiveLevel(firstLevel);
        } else if ((curr.phases ?? [])[0]?.missions?.[0]) {
          // Fallback to legacy phases
          setActiveMission(curr.phases[0].missions[0]);
        }

        // Fetch title
        if (!isJob) {
          try {
            const song = await getSongById(routeId);
            if (song?.title) setSongTitle(song.title);
          } catch { /* non-critical */ }
        } else {
          try {
            const jobStatus = await getPipelineStatus(routeId);
            if (jobStatus?.song_id) {
              const song = await getSongById(jobStatus.song_id);
              if (song?.title) setSongTitle(song.title);
            }
          } catch { /* non-critical */ }
        }
      } catch (err: any) {
        console.error(err);
        setError('Failed to load learning curriculum. ' + err.message);
      } finally {
        setIsLoading(false);
      }
    };
    fetchCurriculum();
  }, [routeId]);

  // Switch global mode → select first mission in that mode
  const handleModeSwitch = (mode: GlobalMode) => {
    setGlobalMode(mode);
    const targetLevels = levels.filter(lv => lv.learningMode === mode);
    const firstMission = targetLevels[0]?.missions?.[0];
    if (firstMission) {
      setActiveMission(firstMission);
      setActiveLevel(targetLevels[0]);
    }
  };

  const handleMissionSelect = (mission: PracticeMission, level: LearningLevel) => {
    setActiveMission(mission);
    setActiveLevel(level);
  };

  const handleMissionComplete = async (score?: number) => {
    if (!activeMission || !routeId) return;
    try {
      const updated = isJobMode
        ? await practiceApi.submitJobMissionProgress(
            routeId,
            activeMission.id,
            'completed',
            score
          )
        : await practiceApi.submitSongMissionProgress(
            routeId,
            activeMission.id,
            'completed',
            score
          );
      setCurriculum(updated);
    } catch (err: any) {
      setError('Could not save mission progress. ' + err.message);
      return;
    }

    // Advance to next mission in same level, or next level
    if (!activeLevel) return;
    const missionIdx = activeLevel.missions.findIndex(m => m.id === activeMission.id);
    if (missionIdx < activeLevel.missions.length - 1) {
      setActiveMission(activeLevel.missions[missionIdx + 1]);
    } else {
      // Try next level
      const levelIdx = levels.findIndex(lv => lv.id === activeLevel.id);
      const nextLevel = levels[levelIdx + 1];
      if (nextLevel?.missions?.[0]) {
        setActiveLevel(nextLevel);
        setActiveMission(nextLevel.missions[0]);
        setGlobalMode(levelToMode(nextLevel.levelNumber));
      } else {
        alert('🎉 Congratulations! You have completed all levels!');
      }
    }
  };

  // ── Loading / Error states ─────────────────────────────────────────────
  if (isLoading) {
    return (
      <div className={styles.studioContainer} style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white', flexDirection: 'column', gap: '12px' }}>
        <div style={{ width: '40px', height: '40px', border: '3px solid #7c3aed', borderTopColor: 'transparent', borderRadius: '50%', animation: 'spin 0.8s linear infinite' }} />
        Loading Curriculum…
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.studioContainer} style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#ef4444' }}>
        {error}
      </div>
    );
  }

  // ── Workspace renderer ─────────────────────────────────────────────────
  const renderWorkspace = () => {
    if (!activeMission) return null;
    const mode = activeLevel?.learningMode ?? 'practice';

    if (mode === 'learn') {
      return (
        <LearnModeWorkspace
          key={activeMission.id}
          mission={activeMission}
          lyricAlignment={lyricAlignment}
          onComplete={handleMissionComplete}
        />
      );
    }

    if (mode === 'perform') {
      return (
        <PerformModeWorkspace
          key={activeMission.id}
          mission={activeMission}
          lyricAlignment={lyricAlignment}
          onComplete={handleMissionComplete}
        />
      );
    }

    // practice (levels 3–4)
    return (
      <PracticeModeWorkspace
        key={activeMission.id}
        mission={activeMission}
        lyricAlignment={lyricAlignment}
        phrases={phrases}
        onComplete={handleMissionComplete}
      />
    );
  };

  const hasNewCurriculum = levels.length > 0;

  return (
    <div style={{ display: 'flex', height: '100vh', background: 'var(--bg-primary)', overflow: 'hidden' }}>

      {/* ── Left Sidebar ──────────────────────────────────────────────── */}
      {sidebarOpen && (
        <div style={{
          width: '300px',
          borderRight: '1px solid var(--border-color)',
          background: 'var(--bg-elevated)',
          overflowY: 'auto',
          display: 'flex',
          flexDirection: 'column',
          flexShrink: 0,
        }}>
          {/* Song title */}
          <div style={{ padding: '20px', borderBottom: '1px solid var(--border-color)' }}>
            <h2 style={{ fontSize: '1rem', fontWeight: 700, margin: 0, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
              {songTitle}
            </h2>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', margin: '4px 0 0 0' }}>
              {hasNewCurriculum ? '5-Step Progressive Curriculum' : 'Structured practice steps'}
            </p>
          </div>

          {/* ── 3-Mode Tabs ─────────────────────────────────────────── */}
          {hasNewCurriculum && (
            <div style={{
              display: 'flex',
              borderBottom: '1px solid var(--border-color)',
            }}>
              {(['learn', 'practice', 'perform'] as GlobalMode[]).map(mode => {
                const m = MODE_META[mode];
                const active = globalMode === mode;
                return (
                  <button
                    key={mode}
                    onClick={() => handleModeSwitch(mode)}
                    title={`${m.emoji} ${m.label} Mode`}
                    style={{
                      flex: 1,
                      padding: '10px 4px',
                      background: active ? 'transparent' : 'rgba(0,0,0,0.15)',
                      border: 'none',
                      borderBottom: active ? `2px solid ${m.color}` : '2px solid transparent',
                      color: active ? m.color : 'var(--text-secondary)',
                      fontWeight: active ? 700 : 500,
                      fontSize: '0.78rem',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease',
                    }}
                  >
                    {m.emoji} {m.label}
                  </button>
                );
              })}
            </div>
          )}

          {/* ── Mission List ─────────────────────────────────────────── */}
          <div style={{ flex: 1, padding: '16px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {hasNewCurriculum ? (
              visibleLevels.length === 0 ? (
                <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', textAlign: 'center', marginTop: '20px' }}>
                  No levels in this mode yet.
                </div>
              ) : (
                visibleLevels.map(level => (
                  <div key={level.id}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px' }}>
                      <span style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                        {level.title}
                      </span>
                      {level.simplified && (
                        <span style={{ fontSize: '0.65rem', background: 'rgba(234,179,8,0.15)', color: '#eab308', borderRadius: '4px', padding: '1px 5px' }}>
                          simplified
                        </span>
                      )}
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                      {level.missions.map(mission => {
                        const isActive = activeMission?.id === mission.id;
                        return (
                          <div
                            key={mission.id}
                            onClick={() => handleMissionSelect(mission, level)}
                            style={{
                              padding: '10px 12px',
                              borderRadius: '8px',
                              cursor: 'pointer',
                              background: isActive ? 'var(--accent-primary)' : 'var(--bg-card)',
                              color: isActive ? 'white' : 'var(--text-primary)',
                              border: isActive ? '1px solid var(--accent-primary)' : '1px solid var(--border-color)',
                              transition: 'all 0.15s ease',
                            }}
                          >
                            <div style={{ fontWeight: 600, fontSize: '0.85rem' }}>{mission.title}</div>
                            {mission.learningGoal && (
                              <div style={{ fontSize: '0.73rem', opacity: isActive ? 0.85 : 0.55, marginTop: '3px', lineHeight: 1.3 }}>
                                {mission.learningGoal.slice(0, 80)}{mission.learningGoal.length > 80 ? '…' : ''}
                              </div>
                            )}
                            <div style={{ display: 'flex', gap: '8px', marginTop: '4px', fontSize: '0.65rem', opacity: 0.6 }}>
                              {mission.progressionMode === 'wait' && <span>⏸ Wait-mode</span>}
                              {mission.bpm && <span>♩ {mission.bpm.toFixed(0)} BPM</span>}
                              {mission.xpReward && <span>⭐ {mission.xpReward} XP</span>}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                ))
              )
            ) : (
              // Fallback: legacy phases
              legacyPhases.map(phase => (
                <div key={phase.id}>
                  <h3 style={{ fontSize: '0.8rem', color: 'var(--accent-primary)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '8px' }}>
                    {phase.title}
                  </h3>
                  {phase.missions.map(mission => {
                    const isActive = activeMission?.id === mission.id;
                    return (
                      <div
                        key={mission.id}
                        onClick={() => setActiveMission(mission)}
                        style={{
                          padding: '10px 12px',
                          borderRadius: '8px',
                          cursor: 'pointer',
                          background: isActive ? 'var(--accent-primary)' : 'var(--bg-card)',
                          color: isActive ? 'white' : 'var(--text-primary)',
                          border: isActive ? '1px solid var(--accent-primary)' : '1px solid var(--border-color)',
                          marginBottom: '6px',
                        }}
                      >
                        <div style={{ fontWeight: 600, fontSize: '0.85rem' }}>{mission.title}</div>
                        <div style={{ fontSize: '0.73rem', opacity: 0.6, marginTop: '3px' }}>{mission.learningGoal}</div>
                      </div>
                    );
                  })}
                </div>
              ))
            )}
          </div>

          {/* Back button */}
          <div style={{ padding: '16px', borderTop: '1px solid var(--border-color)' }}>
            <button
              onClick={() => navigate('/library')}
              style={{
                width: '100%',
                padding: '10px',
                background: 'var(--bg-card)',
                border: '1px solid var(--border-color)',
                borderRadius: '8px',
                color: 'var(--text-secondary)',
                fontSize: '0.85rem',
                cursor: 'pointer',
              }}
            >
              ← Back to Library
            </button>
          </div>
        </div>
      )}

      {/* ── Main Workspace ───────────────────────────────────────────── */}
      <div style={{ flex: 1, overflowY: 'auto', position: 'relative' }}>
        {/* Toggle sidebar button */}
        <button
          onClick={() => setSidebarOpen(o => !o)}
          style={{
            position: 'absolute',
            top: '12px',
            left: '12px',
            zIndex: 10,
            width: '32px',
            height: '32px',
            borderRadius: '8px',
            background: 'var(--bg-card)',
            border: '1px solid var(--border-color)',
            color: 'var(--text-secondary)',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '1rem',
          }}
          title={sidebarOpen ? 'Hide sidebar' : 'Show sidebar'}
        >
          {sidebarOpen ? '◀' : '▶'}
        </button>

        {activeMission ? renderWorkspace() : (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--text-secondary)' }}>
            Select a mission from the sidebar to begin.
          </div>
        )}
      </div>
    </div>
  );
}
