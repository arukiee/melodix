import React, { useState, useEffect, useRef } from 'react';
import { Mic, MicOff, Piano, Wifi, WifiOff, ChevronDown, ChevronUp } from 'lucide-react';
import { liveNoteDetector } from '../services/liveNoteDetector';

export function MicMidiHUD() {
  const [isExpanded, setIsExpanded] = useState(false);
  const [micState, setMicState] = useState<'idle' | 'active' | 'denied'>('idle');
  const [audioLevel, setAudioLevel] = useState(0);
  const [detectedNote, setDetectedNote] = useState<string | null>(null);
  const [midiDevice, setMidiDevice] = useState<string | null>(null);
  const [midiConnected, setMidiConnected] = useState(false);

  const animFrameRef = useRef<number | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const audioCtxRef = useRef<AudioContext | null>(null);

  // Subscribe to live note detector
  useEffect(() => {
    const unsub = liveNoteDetector.subscribe((note) => {
      setDetectedNote(note);
      setTimeout(() => setDetectedNote(null), 800);
    });
    return () => unsub();
  }, []);

  // MIDI device detection
  useEffect(() => {
    if (navigator.requestMIDIAccess) {
      navigator.requestMIDIAccess().then((access) => {
        const checkDevices = () => {
          const inputs = Array.from(access.inputs.values());
          if (inputs.length > 0) {
            setMidiConnected(true);
            setMidiDevice(inputs[0].name || 'MIDI Keyboard');
          } else {
            setMidiConnected(false);
            setMidiDevice(null);
          }
        };
        checkDevices();
        access.onstatechange = checkDevices;
      }).catch(() => {});
    }
  }, []);

  const startMicMonitor = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      setMicState('active');

      const AudioCtx = window.AudioContext || (window as any).webkitAudioContext;
      const ctx = new AudioCtx();
      audioCtxRef.current = ctx;
      const source = ctx.createMediaStreamSource(stream);
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 256;
      source.connect(analyser);
      analyserRef.current = analyser;

      const buf = new Uint8Array(analyser.frequencyBinCount);
      const update = () => {
        if (!analyserRef.current) return;
        analyserRef.current.getByteFrequencyData(buf);
        const avg = buf.reduce((a, b) => a + b, 0) / buf.length;
        setAudioLevel(Math.min(100, Math.round((avg / 128) * 100)));
        animFrameRef.current = requestAnimationFrame(update);
      };
      update();
      await liveNoteDetector.startListening();
    } catch {
      setMicState('denied');
    }
  };

  const stopMicMonitor = () => {
    if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    if (streamRef.current) streamRef.current.getTracks().forEach(t => t.stop());
    if (audioCtxRef.current && audioCtxRef.current.state !== 'closed') audioCtxRef.current.close();
    liveNoteDetector.stopListening();
    setMicState('idle');
    setAudioLevel(0);
  };

  useEffect(() => () => stopMicMonitor(), []);

  const micColor = micState === 'active' ? '#22c55e' : micState === 'denied' ? '#ef4444' : '#6b7280';

  // Level bars for the audio meter
  const bars = 12;

  return (
    <div
      style={{
        position: 'fixed',
        bottom: '24px',
        right: '24px',
        zIndex: 1000,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'flex-end',
        gap: '8px',
        pointerEvents: 'all',
      }}
    >
      {/* Expanded panel */}
      {isExpanded && (
        <div
          style={{
            background: 'rgba(10,10,10,0.92)',
            backdropFilter: 'blur(24px)',
            border: '1px solid rgba(255,255,255,0.1)',
            borderRadius: '20px',
            padding: '20px',
            width: '260px',
            boxShadow: '0 16px 48px rgba(0,0,0,0.7)',
            display: 'flex',
            flexDirection: 'column',
            gap: '16px',
          }}
        >
          <div style={{ fontSize: '0.72rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'rgba(255,255,255,0.4)' }}>
            Audio & MIDI Status
          </div>

          {/* Mic row */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                {micState === 'active' ? <Mic size={16} color={micColor} /> : <MicOff size={16} color={micColor} />}
                <span style={{ fontSize: '0.85rem', fontWeight: 600, color: micColor }}>
                  {micState === 'active' ? 'Mic Active' : micState === 'denied' ? 'Mic Blocked' : 'Mic Off'}
                </span>
              </div>
              <button
                onClick={micState === 'active' ? stopMicMonitor : startMicMonitor}
                style={{
                  padding: '4px 10px',
                  fontSize: '0.72rem',
                  fontWeight: 700,
                  borderRadius: '8px',
                  border: 'none',
                  cursor: 'pointer',
                  background: micState === 'active' ? 'rgba(239,68,68,0.15)' : 'rgba(34,197,94,0.15)',
                  color: micState === 'active' ? '#ef4444' : '#22c55e',
                  transition: 'all 0.2s',
                }}
              >
                {micState === 'active' ? 'Stop' : 'Connect'}
              </button>
            </div>

            {/* Audio level bar */}
            <div style={{ display: 'flex', gap: '3px', alignItems: 'flex-end', height: '24px' }}>
              {Array.from({ length: bars }).map((_, i) => {
                const threshold = (i / bars) * 100;
                const lit = audioLevel > threshold;
                const color = i < bars * 0.5 ? '#22c55e' : i < bars * 0.75 ? '#f59e0b' : '#ef4444';
                return (
                  <div
                    key={i}
                    style={{
                      flex: 1,
                      height: `${40 + i * 5}%`,
                      borderRadius: '2px',
                      background: lit ? color : 'rgba(255,255,255,0.08)',
                      transition: 'background 0.08s ease',
                    }}
                  />
                );
              })}
            </div>

            {/* Detected note */}
            {detectedNote && (
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '8px 12px',
                background: 'rgba(34,197,94,0.1)',
                borderRadius: '10px',
                border: '1px solid rgba(34,197,94,0.25)',
              }}>
                <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#22c55e', animation: 'pulse 1s infinite' }} />
                <span style={{ fontSize: '1rem', fontWeight: 800, color: '#22c55e' }}>{detectedNote}</span>
                <span style={{ fontSize: '0.72rem', color: 'rgba(255,255,255,0.4)' }}>detected</span>
              </div>
            )}
          </div>

          <div style={{ height: '1px', background: 'rgba(255,255,255,0.06)' }} />

          {/* MIDI row */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              {midiConnected ? <Wifi size={16} color="#3b82f6" /> : <WifiOff size={16} color="#6b7280" />}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1px' }}>
                <span style={{ fontSize: '0.82rem', fontWeight: 600, color: midiConnected ? '#3b82f6' : '#6b7280' }}>
                  {midiConnected ? 'MIDI Connected' : 'No MIDI Device'}
                </span>
                {midiDevice && (
                  <span style={{ fontSize: '0.7rem', color: 'rgba(255,255,255,0.4)' }}>{midiDevice}</span>
                )}
              </div>
            </div>
            <div style={{
              width: '8px', height: '8px', borderRadius: '50%',
              background: midiConnected ? '#3b82f6' : '#374151',
              boxShadow: midiConnected ? '0 0 6px #3b82f6' : 'none',
            }} />
          </div>
        </div>
      )}

      {/* Compact floating pill */}
      <button
        onClick={() => setIsExpanded(e => !e)}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          padding: '10px 16px',
          background: 'rgba(10,10,10,0.92)',
          backdropFilter: 'blur(24px)',
          border: `1px solid ${micState === 'active' ? 'rgba(34,197,94,0.3)' : 'rgba(255,255,255,0.1)'}`,
          borderRadius: '40px',
          cursor: 'pointer',
          boxShadow: '0 8px 24px rgba(0,0,0,0.5)',
          transition: 'border-color 0.3s ease',
        }}
      >
        {/* Mic icon */}
        {micState === 'active' ? (
          <div style={{ position: 'relative' }}>
            <Mic size={16} color="#22c55e" />
            <div style={{
              position: 'absolute',
              top: '-2px', right: '-2px',
              width: '6px', height: '6px',
              borderRadius: '50%',
              background: '#22c55e',
              animation: 'hudPulse 1.5s ease-in-out infinite',
            }} />
          </div>
        ) : (
          <MicOff size={16} color="#6b7280" />
        )}

        {/* Level bars mini */}
        <div style={{ display: 'flex', gap: '2px', alignItems: 'flex-end', height: '14px' }}>
          {Array.from({ length: 5 }).map((_, i) => {
            const lit = audioLevel > (i / 5) * 100;
            return (
              <div key={i} style={{
                width: '3px',
                height: `${6 + i * 2}px`,
                borderRadius: '2px',
                background: lit ? '#22c55e' : 'rgba(255,255,255,0.1)',
                transition: 'background 0.08s',
              }} />
            );
          })}
        </div>

        {/* MIDI dot */}
        <div style={{
          width: '7px', height: '7px', borderRadius: '50%',
          background: midiConnected ? '#3b82f6' : '#374151',
          boxShadow: midiConnected ? '0 0 5px #3b82f6' : 'none',
        }} />

        {isExpanded ? <ChevronDown size={14} color="#6b7280" /> : <ChevronUp size={14} color="#6b7280" />}
      </button>

      <style>{`
        @keyframes hudPulse {
          0%, 100% { opacity: 1; transform: scale(1); }
          50% { opacity: 0.4; transform: scale(1.3); }
        }
      `}</style>
    </div>
  );
}
