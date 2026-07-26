import { useState } from 'react';
import { Trophy, Medal, ChevronUp, ChevronDown, Minus, Crown } from 'lucide-react';
import { motion } from 'framer-motion';
import styles from './Leaderboards.module.css';

const MOCK_LEADERBOARD = [
  { rank: 1, name: 'Alex Rivera', score: 15420, trend: 'up', avatar: 'A' },
  { rank: 2, name: 'Sarah Jenkins', score: 14950, trend: 'up', avatar: 'S', isCurrentUser: true },
  { rank: 3, name: 'Maria Chen', score: 14200, trend: 'down', avatar: 'M' },
  { rank: 4, name: 'James Wilson', score: 13800, trend: 'same', avatar: 'J' },
  { rank: 5, name: 'Emma Davis', score: 12100, trend: 'up', avatar: 'E' },
];

export function Leaderboards() {
  const [filter, setFilter] = useState<'friends' | 'global'>('friends');
  const [timeframe, setTimeframe] = useState<'weekly' | 'allTime'>('weekly');

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <div>
          <h1 className={styles.title}>Leaderboards</h1>
          <p className={styles.subtitle}>See how you stack up against the competition.</p>
        </div>
        <div className={styles.filters}>
          <div className={styles.toggleGroup}>
            <button className={`${styles.toggleBtn} ${filter === 'friends' ? styles.active : ''}`} onClick={() => setFilter('friends')}>Friends</button>
            <button className={`${styles.toggleBtn} ${filter === 'global' ? styles.active : ''}`} onClick={() => setFilter('global')}>Global</button>
          </div>
          <div className={styles.toggleGroup}>
            <button className={`${styles.toggleBtn} ${timeframe === 'weekly' ? styles.active : ''}`} onClick={() => setTimeframe('weekly')}>Weekly</button>
            <button className={`${styles.toggleBtn} ${timeframe === 'allTime' ? styles.active : ''}`} onClick={() => setTimeframe('allTime')}>All Time</button>
          </div>
        </div>
      </header>

      <div className={styles.topThree}>
        {/* Rank 2 */}
        <motion.div className={`${styles.podium} ${styles.rank2}`} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
          <div className={styles.podiumAvatar}>
            {MOCK_LEADERBOARD[1].avatar}
            <div className={styles.medalBadge} style={{ background: '#C0C0C0' }}>2</div>
          </div>
          <h3 className={styles.podiumName}>{MOCK_LEADERBOARD[1].name}</h3>
          <p className={styles.podiumScore}>{MOCK_LEADERBOARD[1].score} XP</p>
        </motion.div>

        {/* Rank 1 */}
        <motion.div className={`${styles.podium} ${styles.rank1}`} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
          <Crown size={32} color="#FFD700" style={{ marginBottom: '8px' }} />
          <div className={styles.podiumAvatar}>
            {MOCK_LEADERBOARD[0].avatar}
            <div className={styles.medalBadge} style={{ background: '#FFD700' }}>1</div>
          </div>
          <h3 className={styles.podiumName}>{MOCK_LEADERBOARD[0].name}</h3>
          <p className={styles.podiumScore}>{MOCK_LEADERBOARD[0].score} XP</p>
        </motion.div>

        {/* Rank 3 */}
        <motion.div className={`${styles.podium} ${styles.rank3}`} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
          <div className={styles.podiumAvatar}>
            {MOCK_LEADERBOARD[2].avatar}
            <div className={styles.medalBadge} style={{ background: '#CD7F32' }}>3</div>
          </div>
          <h3 className={styles.podiumName}>{MOCK_LEADERBOARD[2].name}</h3>
          <p className={styles.podiumScore}>{MOCK_LEADERBOARD[2].score} XP</p>
        </motion.div>
      </div>

      <div className={styles.list}>
        {MOCK_LEADERBOARD.slice(3).map((user, index) => (
          <motion.div 
            key={user.rank} 
            className={`${styles.row} ${user.isCurrentUser ? styles.currentUser : ''}`}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.3 + index * 0.1 }}
          >
            <div className={styles.rankCol}>
              <span className={styles.rankNum}>{user.rank}</span>
              {user.trend === 'up' && <ChevronUp size={16} color="var(--status-success)" />}
              {user.trend === 'down' && <ChevronDown size={16} color="var(--status-error)" />}
              {user.trend === 'same' && <Minus size={16} color="var(--text-muted)" />}
            </div>
            <div className={styles.avatarCol}>
              <div className={styles.rowAvatar}>{user.avatar}</div>
            </div>
            <div className={styles.nameCol}>
              <span className={styles.nameText}>{user.name}</span>
              {user.isCurrentUser && <span className={styles.youBadge}>You</span>}
            </div>
            <div className={styles.scoreCol}>
              {user.score} XP
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
