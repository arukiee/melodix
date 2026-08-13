import React, { useState } from 'react';
import { X, Play, Download, Loader, Music, BookOpen, Clock, AlertCircle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { searchApi, type SearchResult } from '../../api/search';

interface Props {
  song: SearchResult;
  onClose: () => void;
}

export const SongDetailModal: React.FC<Props> = ({ song, onClose }) => {
  const [importing, setImporting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const navigate = useNavigate();

  const handleImport = async () => {
    setImporting(true);
    setError(null);
    try {
      const res = await searchApi.importFromSearch(song);
      if (res.success && res.song_id) {
        setSuccess(res.message || "Successfully imported!");
        setTimeout(() => {
          onClose();
          navigate(`/song/${res.song_id}`);
        }, 1500);
      } else {
        setError(res.message || "Failed to import song");
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || "Failed to import song");
    } finally {
      setImporting(false);
    }
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0, left: 0, right: 0, bottom: 0,
      backgroundColor: 'rgba(0,0,0,0.5)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000,
      padding: '20px'
    }}>
      <div style={{
        background: 'var(--surface-color)',
        borderRadius: 'var(--radius-card)',
        width: '100%',
        maxWidth: '500px',
        boxShadow: 'var(--shadow-lg)',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden'
      }}>
        <div style={{ padding: '20px', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2 style={{ margin: 0, fontSize: '1.25rem' }}>Song Details</h2>
          <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-secondary)' }}>
            <X size={24} />
          </button>
        </div>

        <div style={{ padding: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: '16px', marginBottom: '24px' }}>
            {song.thumbnailUrl ? (
              <img src={song.thumbnailUrl} alt={song.title} style={{ width: '100px', height: '100px', objectFit: 'cover', borderRadius: '8px' }} />
            ) : (
              <div style={{ width: '100px', height: '100px', background: 'var(--bg-color)', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Music size={40} color="var(--text-secondary)" />
              </div>
            )}
            <div>
              <h3 style={{ margin: '0 0 8px 0', fontSize: '1.5rem' }}>{song.title}</h3>
              <p style={{ margin: '0 0 12px 0', color: 'var(--text-secondary)', fontSize: '1.1rem' }}>{song.artist}</p>
              
              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                <span style={{ fontSize: '0.8rem', padding: '4px 10px', background: 'rgba(59, 130, 246, 0.1)', color: '#3b82f6', borderRadius: '12px' }}>
                  {song.provider}
                </span>
                <span style={{ fontSize: '0.8rem', padding: '4px 10px', background: 'var(--bg-color)', borderRadius: '12px' }}>
                  {song.difficulty}
                </span>
              </div>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '32px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-secondary)' }}>
              <Clock size={18} />
              <span>{song.duration ? `${Math.floor(song.duration / 60)}:${(song.duration % 60).toString().padStart(2, '0')}` : 'Unknown duration'}</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-secondary)' }}>
              <BookOpen size={18} />
              <span>{song.hasMidi ? 'Interactive Lesson' : (song.hasChords ? 'Chords Only' : 'Preview Only')}</span>
            </div>
          </div>

          {error && (
            <div style={{ padding: '12px', background: 'rgba(239, 68, 68, 0.1)', color: '#ef4444', borderRadius: '8px', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <AlertCircle size={18} />
              <span style={{ fontSize: '0.9rem' }}>{error}</span>
            </div>
          )}

          {success && (
            <div style={{ padding: '12px', background: 'rgba(16, 185, 129, 0.1)', color: '#10b981', borderRadius: '8px', marginBottom: '20px', textAlign: 'center' }}>
              {success}
            </div>
          )}

          <button
            onClick={handleImport}
            disabled={importing || !!success}
            style={{
              width: '100%',
              padding: '14px',
              background: success ? '#10b981' : 'var(--accent-primary)',
              color: 'white',
              border: 'none',
              borderRadius: 'var(--radius-button)',
              fontSize: '1.1rem',
              fontWeight: '600',
              cursor: importing || success ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '12px',
              transition: 'background 0.2s ease'
            }}
          >
            {importing ? (
              <Loader size={20} className="spin" />
            ) : success ? (
              <Play size={20} />
            ) : (
              <Download size={20} />
            )}
            {importing ? 'Importing & Analyzing...' : success ? 'Ready to Play' : 'Import & Practice'}
          </button>
        </div>
      </div>
    </div>
  );
};
