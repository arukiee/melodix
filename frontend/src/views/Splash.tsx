import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Music } from 'lucide-react';
import styles from './Splash.module.css';

export function Splash() {
  const navigate = useNavigate();

  useEffect(() => {
    const timer = setTimeout(() => {
      navigate('/login');
    }, 2500);

    return () => clearTimeout(timer);
  }, [navigate]);

  return (
    <div className={styles.splashContainer}>
      <div className={styles.logo}>
        <Music size={48} color="var(--accent-primary)" />
        Melodix
      </div>
      <div className={styles.pulsingText}>Tuning the piano...</div>
    </div>
  );
}
