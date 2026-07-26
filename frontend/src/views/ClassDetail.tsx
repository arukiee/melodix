import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Plus, Users, LayoutDashboard, Settings } from 'lucide-react';
import { motion } from 'framer-motion';
import { Button } from '../components/Button';
import styles from './ClassDetail.module.css';

export function ClassDetail() {
  const { id } = useParams();
  const navigate = useNavigate();

  const mockClass = {
    id: id,
    name: 'Intermediate Piano',
    students: 8,
    schedule: 'Tuesdays & Thursdays, 4:00 PM',
    description: 'Focusing on scales, basic sight-reading, and two-hand independence.'
  };

  return (
    <motion.div 
      className={styles.container}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
    >
      <header className={styles.header}>
        <div className={styles.headerLeft}>
          <button className={styles.backBtn} onClick={() => navigate(-1)}>
            <ArrowLeft size={20} />
          </button>
          <div>
            <h1 className={styles.name}>{mockClass.name}</h1>
            <p className={styles.meta}>
              {mockClass.students} Students • {mockClass.schedule}
            </p>
          </div>
        </div>
        <div className={styles.headerActions}>
          <Button variant="secondary" onClick={() => alert('Opening class settings...')}>
            <Settings size={16} style={{ marginRight: '8px' }} />
            Settings
          </Button>
          <Button variant="primary" onClick={() => alert('Assigning lesson to class...')}>
            <Plus size={16} style={{ marginRight: '8px' }} />
            New Assignment
          </Button>
        </div>
      </header>

      <div className={styles.content}>
        <div className={styles.mainCol}>
          <section className={styles.section}>
            <h2 className={styles.sectionTitle}>Students</h2>
            <div className={styles.card}>
              <div className={styles.emptyState}>
                <Users size={32} color="var(--text-muted)" style={{ marginBottom: '12px' }} />
                <p>No students enrolled yet.</p>
                <Button variant="secondary" style={{ marginTop: '16px' }}>Add Students</Button>
              </div>
            </div>
          </section>
        </div>
        <div className={styles.sideCol}>
          <section className={styles.section}>
            <h2 className={styles.sectionTitle}>Class Analytics</h2>
            <div className={styles.card}>
              <div className={styles.emptyState}>
                <LayoutDashboard size={32} color="var(--text-muted)" style={{ marginBottom: '12px' }} />
                <p>Not enough data to display analytics.</p>
              </div>
            </div>
          </section>
        </div>
      </div>
    </motion.div>
  );
}
