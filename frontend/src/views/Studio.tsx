import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { PracticeWorkspace } from '../components/Studio/PracticeWorkspace';
import type { PracticeMission, PracticePhase } from '../api/practice';
import { getPipelineCurriculum, getPipelineStatus, getSongById } from '../api/audio';
import styles from './Studio.module.css';

export function Studio() {
  const navigate = useNavigate();
  const { songId: jobId } = useParams<{ songId: string }>(); 
  const [phases, setPhases] = useState<PracticePhase[]>([]);
  const [activeMission, setActiveMission] = useState<PracticeMission | null>(null);
  const [songTitle, setSongTitle] = useState('AI Curriculum Practice');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchCurriculum = async () => {
      if (!jobId) return;
      try {
        setIsLoading(true);
        const [curriculum, jobStatus] = await Promise.all([
          getPipelineCurriculum(jobId),
          getPipelineStatus(jobId).catch(() => null),
        ]);

        setPhases(curriculum.phases || []);

        if (curriculum.phases && curriculum.phases.length > 0) {
          const firstPhase = curriculum.phases[0];
          if (firstPhase.missions && firstPhase.missions.length > 0) {
            setActiveMission(firstPhase.missions[0]);
          }
        }

        const selectedSongId = jobStatus?.song_id;
        if (selectedSongId) {
          try {
            const song = await getSongById(selectedSongId);
            if (song?.title) {
              setSongTitle(song.title);
            }
          } catch (songErr) {
            console.warn('Could not load selected song title for this curriculum:', songErr);
          }
        }
      } catch (err: any) {
        console.error(err);
        setError("Failed to load learning curriculum. " + err.message);
      } finally {
        setIsLoading(false);
      }
    };
    fetchCurriculum();
  }, [jobId]);

  if (isLoading) {
    return <div className={styles.studioContainer} style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white' }}>Loading Curriculum...</div>;
  }

  if (error || phases.length === 0 || !activeMission) {
    return <div className={styles.studioContainer} style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#ef4444' }}>{error || "Failed to create curriculum"}</div>;
  }

  return (
    <div style={{ display: 'flex', height: '100vh', background: 'var(--bg-primary)' }}>
      {/* Curriculum Sidebar */}
      <div style={{ width: '300px', borderRight: '1px solid var(--border-color)', background: 'var(--bg-elevated)', overflowY: 'auto', display: 'flex', flexDirection: 'column' }}>
        <div style={{ padding: '20px', borderBottom: '1px solid var(--border-color)' }}>
          <h2 style={{ fontSize: '1.2rem', fontWeight: 'bold', margin: 0 }}>Learning Plan</h2>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', margin: '4px 0 0 0' }}>Structured practice steps</p>
        </div>
        
        <div style={{ flex: 1, padding: '16px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {phases.map((phase) => (
            <div key={phase.id}>
              <h3 style={{ fontSize: '0.9rem', color: 'var(--accent-primary)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '12px' }}>
                {phase.title}
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {phase.missions.map((mission) => {
                  const isActive = activeMission.id === mission.id;
                  return (
                    <div
                      key={mission.id}
                      onClick={() => setActiveMission(mission)}
                      style={{
                        padding: '12px',
                        borderRadius: '8px',
                        cursor: 'pointer',
                        background: isActive ? 'var(--accent-primary)' : 'var(--bg-card)',
                        color: isActive ? 'white' : 'var(--text-primary)',
                        border: isActive ? '1px solid var(--accent-primary)' : '1px solid var(--border-color)',
                        transition: 'all 0.2s ease',
                      }}
                    >
                      <div style={{ fontWeight: 'bold', fontSize: '0.95rem' }}>{mission.title}</div>
                      <div style={{ fontSize: '0.8rem', opacity: isActive ? 0.9 : 0.6, marginTop: '4px' }}>
                        {mission.learningGoal}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Main Workspace */}
      <div style={{ flex: 1, padding: '24px', overflowY: 'auto' }}>
        <PracticeWorkspace
          // Force remount when switching missions so the internal timers and recorders reset properly
          key={activeMission.id}
          songTitle={songTitle}
          mission={activeMission}
          onBack={() => navigate('/learn')}
          onComplete={() => {
             // Basic progression mock
             alert("Mission completed! Moving to next step is not fully automated yet.");
          }}
        />
      </div>
    </div>
  );
}
