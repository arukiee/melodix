import React, { useState } from 'react';
import { Upload, FileText, Music, CheckCircle, AlertTriangle, Loader, ArrowRight, Info, AlertCircle } from 'lucide-react';

interface ChordInfo {
  measure: number;
  pitches: string[];
  detected_chord: string;
}

interface MissionInfo {
  id: string;
  title: string;
  type: string;
  bpm: number;
  learningGoal: string;
  xpReward: number;
}

interface ImportPreview {
  title: string;
  composer: string;
  key_signature: string;
  time_signature: string;
  bpm: number;
  measure_count: number;
  note_count: number;
  detected_chords: ChordInfo[];
  generated_missions: MissionInfo[];
  validation_warnings: string[];
}

interface ImportSongProps {
  onImportSuccess?: (songTitle: string) => void;
}

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const ImportSong: React.FC<ImportSongProps> = ({ onImportSuccess }) => {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<ImportPreview | null>(null);
  const [loading, setLoading] = useState(false);
  const [stepText, setStepText] = useState<string>('');
  const [commitResult, setCommitResult] = useState<{ success: boolean; message: string; song_id?: string } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0];
    if (selected) {
      setFile(selected);
      setPreview(null);
      setCommitResult(null);
      setError(null);
    }
  };

  const handlePreview = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    setStepText('Analyzing score structures & extracting musical timeline...');

    try {
      const formData = new FormData();
      formData.append('file', file);

      const res = await fetch(`${API_BASE}/api/v1/import/preview`, {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Preview failed. Please check the file format.');
      }

      const data = await res.json();
      setPreview(data);
    } catch (err: any) {
      setError(err.message || 'Failed to preview file');
    } finally {
      setLoading(false);
      setStepText('');
    }
  };

  const handleCommit = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    setStepText('Persisting song package & generating curriculum missions...');

    try {
      const formData = new FormData();
      formData.append('file', file);

      const res = await fetch(`${API_BASE}/api/v1/import/commit`, {
        method: 'POST',
        body: formData,
      });

      const data = await res.json();
      if (data.success) {
        setCommitResult({ success: true, message: data.message, song_id: data.song_id });
      } else {
        setCommitResult({ success: false, message: data.message });
      }
    } catch (err: any) {
      setError(err.message || 'Failed to import song');
    } finally {
      setLoading(false);
      setStepText('');
    }
  };

  // Classify warnings vs critical blocking errors
  const criticalErrors = preview?.validation_warnings.filter(w => 
    w.toLowerCase().includes('empty') || 
    w.toLowerCase().includes('invalid duration') || 
    w.toLowerCase().includes('no parsed notes') ||
    w.toLowerCase().includes('missing note name')
  ) || [];

  const softWarnings = preview?.validation_warnings.filter(w => !criticalErrors.includes(w)) || [];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', maxWidth: '800px', margin: '0 auto' }}>
      {/* Upload Box */}
      <div
        style={{
          padding: '32px',
          backgroundColor: 'var(--bg-card)',
          borderRadius: 'var(--radius-card)',
          border: '2px dashed var(--border-color)',
          textAlign: 'center',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: '16px',
        }}
      >
        <Upload size={44} color="var(--accent-primary)" />
        <div>
          <h3 style={{ margin: '0 0 6px 0', fontSize: '1.25rem', fontWeight: 'bold' }}>Import Music Score</h3>
          <p style={{ margin: 0, fontSize: '0.88rem', color: 'var(--text-secondary)' }}>
            Supports MusicXML (.xml, .musicxml) from MuseScore, Finale, Sibelius, or MIDI (.mid)
          </p>
        </div>

        <label
          style={{
            padding: '10px 24px',
            backgroundColor: 'var(--accent-primary)',
            color: 'white',
            borderRadius: 'var(--radius-button)',
            cursor: 'pointer',
            fontWeight: 'bold',
            fontSize: '0.9rem',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
          }}
        >
          <FileText size={16} />
          Choose File
          <input
            type="file"
            accept=".xml,.musicxml,.mid,.midi"
            onChange={handleFileSelect}
            style={{ display: 'none' }}
          />
        </label>

        {file && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginTop: '4px' }}>
            <span style={{ fontSize: '0.88rem', color: 'var(--text-secondary)' }}>
              Selected: <strong>{file.name}</strong> ({(file.size / 1024).toFixed(1)} KB)
            </span>
            <button
              onClick={handlePreview}
              disabled={loading}
              style={{
                padding: '8px 16px',
                backgroundColor: '#3b82f6',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer',
                fontWeight: 'bold',
                fontSize: '0.82rem',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
              }}
            >
              {loading ? <Loader size={14} className="animate-spin" /> : <Music size={14} />}
              {loading ? 'Analyzing...' : 'Preview Import'}
            </button>
          </div>
        )}

        {/* Step Progress Indicator */}
        {loading && stepText && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#3b82f6', fontSize: '0.85rem', fontWeight: '500' }}>
            <Loader size={14} className="animate-spin" />
            <span>{stepText}</span>
          </div>
        )}
      </div>

      {/* Error Message */}
      {error && (
        <div style={{ padding: '14px 18px', backgroundColor: 'rgba(239, 68, 68, 0.1)', border: '1px solid #ef4444', borderRadius: '8px', color: '#ef4444', fontSize: '0.88rem', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <AlertCircle size={18} />
          <span>{error}</span>
        </div>
      )}

      {/* Preview Card */}
      {preview && (
        <div
          style={{
            padding: '24px',
            backgroundColor: 'var(--bg-card)',
            borderRadius: 'var(--radius-card)',
            border: '1px solid var(--border-color)',
            display: 'flex',
            flexDirection: 'column',
            gap: '20px',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <h3 style={{ margin: '0 0 4px 0', fontSize: '1.35rem', fontWeight: 'bold' }}>{preview.title}</h3>
              <p style={{ margin: 0, fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Composer: {preview.composer}</p>
            </div>
            <span style={{ padding: '4px 12px', backgroundColor: 'rgba(59, 130, 246, 0.1)', color: '#3b82f6', borderRadius: '12px', fontSize: '0.75rem', fontWeight: 'bold' }}>
              Import Preview
            </span>
          </div>

          <hr style={{ border: 0, borderTop: '1px solid var(--border-color)', margin: 0 }} />

          {/* Score Overview Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px' }}>
            {[
              { label: 'Key Signature', value: preview.key_signature },
              { label: 'Time Signature', value: preview.time_signature },
              { label: 'Target Tempo', value: `${preview.bpm} BPM` },
              { label: 'Total Measures', value: String(preview.measure_count) },
              { label: 'Parsed Notes', value: String(preview.note_count) },
              { label: 'Harmonic Chords', value: String(preview.detected_chords.length) },
            ].map((item) => (
              <div key={item.label} style={{ padding: '10px', backgroundColor: 'rgba(255,255,255,0.03)', borderRadius: '6px', textAlign: 'center' }}>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{item.label}</div>
                <div style={{ fontSize: '1rem', fontWeight: 'bold', marginTop: '2px' }}>{item.value}</div>
              </div>
            ))}
          </div>

          {/* Critical Errors Notice */}
          {criticalErrors.length > 0 && (
            <div style={{ padding: '12px 16px', backgroundColor: 'rgba(239, 68, 68, 0.08)', border: '1px solid rgba(239, 68, 68, 0.3)', borderRadius: '6px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '6px' }}>
                <AlertCircle size={16} color="#ef4444" />
                <strong style={{ fontSize: '0.85rem', color: '#ef4444' }}>Critical Parser Issues (Action Required)</strong>
              </div>
              {criticalErrors.map((err, i) => (
                <div key={i} style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', paddingLeft: '22px' }}>• {err}</div>
              ))}
            </div>
          )}

          {/* Soft Validation Warnings */}
          {softWarnings.length > 0 && (
            <div style={{ padding: '12px 16px', backgroundColor: 'rgba(245, 158, 11, 0.08)', border: '1px solid rgba(245, 158, 11, 0.3)', borderRadius: '6px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '6px' }}>
                <AlertTriangle size={16} color="#f59e0b" />
                <strong style={{ fontSize: '0.85rem', color: '#f59e0b' }}>Notation Warnings & Informational Notes</strong>
              </div>
              {softWarnings.map((w, i) => (
                <div key={i} style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', paddingLeft: '22px' }}>• {w}</div>
              ))}
            </div>
          )}

          {/* Information Banner on Skipped Elements */}
          <div style={{ padding: '12px 16px', backgroundColor: 'rgba(59, 130, 246, 0.06)', border: '1px solid rgba(59, 130, 246, 0.2)', borderRadius: '6px', display: 'flex', alignItems: 'flex-start', gap: '10px' }}>
            <Info size={16} color="#3b82f6" style={{ marginTop: '2px', flexShrink: 0 }} />
            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: '1.4' }}>
              <strong>Score Engine Ingestion Note:</strong> Note pitches, durations, measure divisions, and chords have been extracted into the pitch timeline. Ornaments (trills, turns) and explicit dynamics text markings are currently mapped to standard velocity defaults.
            </div>
          </div>

          {/* Detected Chords */}
          {preview.detected_chords.length > 0 && (
            <div>
              <h4 style={{ margin: '0 0 8px 0', fontSize: '0.9rem', fontWeight: 'bold' }}>Harmonic Structure (Detected Chords)</h4>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                {preview.detected_chords.map((c, i) => (
                  <span key={i} style={{ padding: '4px 10px', backgroundColor: 'rgba(16, 185, 129, 0.1)', border: '1px solid rgba(16, 185, 129, 0.3)', borderRadius: '4px', fontSize: '0.75rem', color: '#10b981' }}>
                    M{c.measure + 1}: {c.detected_chord}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Generated Missions */}
          <div>
            <h4 style={{ margin: '0 0 8px 0', fontSize: '0.9rem', fontWeight: 'bold' }}>Generated Learning Missions</h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {preview.generated_missions.map((m) => (
                <div key={m.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 14px', backgroundColor: 'rgba(255,255,255,0.03)', borderRadius: '6px', fontSize: '0.85rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <CheckCircle size={15} color="#10b981" />
                    <div>
                      <div style={{ fontWeight: '600' }}>{m.title}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{m.learningGoal}</div>
                    </div>
                  </div>
                  <span style={{ fontSize: '0.75rem', color: '#f59e0b', fontWeight: 'bold' }}>+{m.xpReward} XP</span>
                </div>
              ))}
            </div>
          </div>

          <hr style={{ border: 0, borderTop: '1px solid var(--border-color)', margin: 0 }} />

          {/* Commit Button */}
          <button
            onClick={handleCommit}
            disabled={loading || criticalErrors.length > 0}
            style={{
              width: '100%',
              padding: '14px',
              backgroundColor: criticalErrors.length > 0 ? '#6b7280' : '#10b981',
              color: 'white',
              border: 'none',
              borderRadius: 'var(--radius-button)',
              cursor: criticalErrors.length > 0 ? 'not-allowed' : 'pointer',
              fontWeight: 'bold',
              fontSize: '1rem',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
            }}
          >
            {loading ? <Loader size={18} className="animate-spin" /> : <CheckCircle size={18} />}
            {loading ? 'Importing Song Package...' : 'Commit & Save to Curriculum'}
          </button>
        </div>
      )}

      {/* Commit Result Success Panel */}
      {commitResult && (
        <div style={{ padding: '20px', backgroundColor: commitResult.success ? 'rgba(16, 185, 129, 0.08)' : 'rgba(239, 68, 68, 0.08)', border: `1px solid ${commitResult.success ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`, borderRadius: '8px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '1rem', fontWeight: 'bold', color: commitResult.success ? '#10b981' : '#ef4444' }}>
            {commitResult.success ? <CheckCircle size={20} /> : <AlertCircle size={20} />}
            <span>{commitResult.message}</span>
          </div>

          {commitResult.success && onImportSuccess && preview && (
            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '8px' }}>
              <button
                onClick={() => onImportSuccess(preview.title)}
                style={{
                  padding: '10px 20px',
                  backgroundColor: 'var(--accent-primary)',
                  color: 'white',
                  border: 'none',
                  borderRadius: 'var(--radius-button)',
                  cursor: 'pointer',
                  fontWeight: 'bold',
                  fontSize: '0.88rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                }}
              >
                <span>View in Discover & Practice</span>
                <ArrowRight size={16} />
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ImportSong;
