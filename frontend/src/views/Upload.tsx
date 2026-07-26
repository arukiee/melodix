import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { UploadCloud, Link } from 'lucide-react';
import { motion } from 'framer-motion';
import { Button } from '../components/Button';
import styles from './Upload.module.css';

export function Upload() {
  const navigate = useNavigate();
  const [dragActive, setDragActive] = useState(false);
  const [youtubeUrl, setYoutubeUrl] = useState('');

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      navigate('/processing');
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      navigate('/processing');
    }
  };

  const handleYoutubeSubmit = () => {
    if (youtubeUrl) {
      navigate('/processing');
    }
  };

  return (
    <motion.div 
      className={styles.upload}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <header className={styles.header}>
        <h1 className={styles.title}>Learn Any Song</h1>
        <p className={styles.subtitle}>Upload sheet music, a MIDI file, or paste a YouTube link. Our AI will generate a personalized lesson.</p>
      </header>

      <div 
        className={`${styles.uploadCard} ${dragActive ? styles.dragActive : ''}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <UploadCloud size={48} className={styles.uploadIcon} />
        <h3 className={styles.uploadTitle}>Drag & drop your file here</h3>
        <p className={styles.uploadDesc}>Supports MIDI, MusicXML, PDF, and MP3</p>
        
        <input 
          type="file" 
          id="file-upload" 
          style={{ display: 'none' }} 
          onChange={handleFileInput}
          accept=".mid,.midi,.xml,.mxl,.pdf,.mp3"
        />
        <Button variant="secondary" onClick={() => document.getElementById('file-upload')?.click()}>
          Browse Files
        </Button>
      </div>

      <div className={styles.divider}>Or</div>

      <div className={styles.youtubeInput}>
        <input 
          type="text" 
          className={styles.inputField} 
          placeholder="Paste a YouTube URL to transcribe..." 
          value={youtubeUrl}
          onChange={(e) => setYoutubeUrl(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleYoutubeSubmit()}
        />
        <Button variant="primary" onClick={handleYoutubeSubmit} disabled={!youtubeUrl}>
          <Link size={18} style={{ marginRight: '8px' }} />
          Transcribe
        </Button>
      </div>
    </motion.div>
  );
}
