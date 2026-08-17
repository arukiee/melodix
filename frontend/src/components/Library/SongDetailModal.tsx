import React, { useState } from 'react';
import { X, Play, Loader, Music, Check, X as XIcon, AlertCircle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { searchApi, type SearchResult } from '../../api/search';
import { importSong, uploadAudio } from '../../api/audio';

interface Props {
  song: SearchResult;
  onClose: () => void;
}

type Difficulty = 'EASY' | 'MEDIUM' | 'HARD' | 'EXPERT';

export const SongDetailModal: React.FC<Props> = ({ song, onClose }) => {
  const [importing, setImporting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [difficulty, setDifficulty] = useState<Difficulty>('MEDIUM');
  
  const navigate = useNavigate();

  const handleImport = async () => {
    setImporting(true);
    setError(null);
    try {
      // 1. Ensure song is in our DB
      const res = await searchApi.importFromSearch(song);
      if (!res.success || !res.song_id) {
        throw new Error(res.message || "Failed to sync song metadata");
      }
      
      const songId = res.song_id;

      // 2. Ask the backend to resolve the source and analyze
      try {
        const pipelineRes = await importSong(songId);
        // It will return a processing_job_id from the source discovery
        if (pipelineRes.processing_job_id) {
          navigate(`/processing/${pipelineRes.processing_job_id}`);
        } else {
          navigate(`/song/${songId}?diff=${difficulty.toLowerCase()}`);
        }
        onClose();
      } catch (importErr: any) {
        // If it failed due to missing source (400), we show the error and the upload box
        if (importErr.message.includes('No valid MIDI or Audio source found')) {
          setError("This song doesn't currently have an analyzable source. Try another version or upload a fallback file below.");
          // We attach the songId to the component state so the upload handler can use it
          setPendingUploadSongId(songId);
        } else {
          throw importErr;
        }
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || "Failed to process song");
    } finally {
      setImporting(false);
    }
  };

  const [pendingUploadSongId, setPendingUploadSongId] = useState<string | null>(null);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0 || !pendingUploadSongId) return;
    
    const file = e.target.files[0];
    setImporting(true);
    setError(null);
    try {
      const res = await uploadAudio(file, pendingUploadSongId);
      // Route to the processing tracker!
      navigate(`/processing/${res.processing_job_id}`);
      onClose();
    } catch (err: any) {
      setError(err.message || "Failed to upload file");
    } finally {
      setImporting(false);
    }
  };

  // True pipeline states
  const hasChords = song.hasChords || song.provider.toLowerCase() === 'youtube';
  const hasMidi = song.hasMidi;
  const hasAudio = false; 
  const hasTranscription = false;

  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
      backgroundColor: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(4px)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      zIndex: 1000, padding: '20px'
    }}>
      <div style={{
        background: 'var(--surface-color)',
        borderRadius: '12px',
        width: '100%',
        maxWidth: '460px',
        boxShadow: 'var(--shadow-xl)',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        border: '1px solid var(--border-color)'
      }}>
        {/* Header */}
        <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2 style={{ margin: 0, fontSize: '1.2rem', fontWeight: 600 }}>Song Details</h2>
          <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-secondary)' }}>
            <X size={20} />
          </button>
        </div>

        <div style={{ padding: '24px' }}>
          {/* Track Info */}
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: '16px', marginBottom: '24px' }}>
            {song.thumbnailUrl ? (
              <img src={song.thumbnailUrl} alt={song.title} style={{ width: '80px', height: '80px', objectFit: 'cover', borderRadius: '8px' }} />
            ) : (
              <div style={{ width: '80px', height: '80px', background: 'var(--bg-color)', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Music size={32} color="var(--text-secondary)" />
              </div>
            )}
            <div style={{ flex: 1, overflow: 'hidden' }}>
              <h3 style={{ margin: '0 0 4px 0', fontSize: '1.25rem', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }} title={song.title}>
                {song.title}
              </h3>
              <p style={{ margin: '0 0 8px 0', color: 'var(--text-secondary)', fontSize: '1rem', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                {song.artist}
              </p>
              <div style={{ display: 'flex', gap: '8px', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                <span>{song.duration ? `${Math.floor(song.duration / 60)}:${(song.duration % 60).toString().padStart(2, '0')}` : 'Unknown'}</span>
                <span>•</span>
                <span>{song.provider}</span>
              </div>
            </div>
          </div>

          <hr style={{ border: 'none', borderTop: '1px solid var(--border-color)', margin: '0 0 24px 0' }} />

          {/* Sources */}
          <div style={{ marginBottom: '24px' }}>
            <h4 style={{ margin: '0 0 12px 0', fontSize: '1rem', fontWeight: 600 }}>Available source</h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <SourceItem label="Chords" available={hasChords} />
              <SourceItem label="Piano transcription" available={hasTranscription} />
              <SourceItem label="MIDI" available={hasMidi} />
              <SourceItem label="Audio" available={hasAudio} />
            </div>
          </div>

          {/* Difficulty Selection */}
          <div style={{ marginBottom: '32px' }}>
            <h4 style={{ margin: '0 0 12px 0', fontSize: '1rem', fontWeight: 600 }}>Difficulty</h4>
            <div style={{ display: 'flex', gap: '12px' }}>
              {(['EASY', 'MEDIUM', 'HARD', 'EXPERT'] as Difficulty[]).map(level => (
                <label key={level} style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer', fontSize: '0.9rem' }}>
                  <input 
                    type="radio" 
                    name="difficulty" 
                    value={level} 
                    checked={difficulty === level}
                    onChange={(e) => setDifficulty(e.target.value as Difficulty)}
                    style={{ accentColor: 'var(--accent-primary)' }}
                  />
                  {level.charAt(0) + level.slice(1).toLowerCase()}
                </label>
              ))}
            </div>
          </div>

          {/* Error Banner & Upload Box */}
          {error && (
            <div style={{ padding: '16px', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)', color: '#ef4444', borderRadius: '8px', marginBottom: '20px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px', lineHeight: 1.4 }}>
                <AlertCircle size={18} style={{ flexShrink: 0, marginTop: '2px' }} />
                <span style={{ fontSize: '0.9rem' }}>{error}</span>
              </div>
              
              {pendingUploadSongId && (
                <div style={{ marginTop: '8px' }}>
                  <label 
                    style={{ 
                      display: 'inline-block', 
                      background: 'var(--bg-card)', 
                      padding: '10px 16px', 
                      borderRadius: '6px', 
                      cursor: 'pointer',
                      border: '1px solid var(--border-color)',
                      color: 'var(--text-primary)',
                      fontSize: '0.9rem',
                      fontWeight: 500
                    }}
                  >
                    Select fallback Audio or MIDI file to analyze
                    <input 
                      type="file" 
                      accept=".wav,.mp3,.flac,.mid,.midi" 
                      style={{ display: 'none' }} 
                      onChange={handleFileUpload}
                      disabled={importing}
                    />
                  </label>
                </div>
              )}
            </div>
          )}

          {!pendingUploadSongId && (
            <button
              onClick={handleImport}
              disabled={importing}
              style={{
                width: '100%',
                padding: '14px',
                background: 'var(--accent-primary)',
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                fontSize: '1rem',
                fontWeight: '600',
                cursor: importing ? 'not-allowed' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px',
                transition: 'opacity 0.2s ease',
                opacity: importing ? 0.7 : 1
              }}
            >
              {importing ? <Loader size={20} className="spin" /> : <Play size={20} />}
              {importing ? 'Finding best source...' : 'Analyze & Create Learning Plan'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

const SourceItem = ({ label, available }: { label: string, available: boolean }) => (
  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: available ? 'var(--text-primary)' : 'var(--text-muted)' }}>
    {available ? <Check size={16} color="#10b981" /> : <XIcon size={16} />}
    <span style={{ fontSize: '0.95rem' }}>{label}</span>
  </div>
);
