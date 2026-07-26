import { useState } from 'react';
import { Search, UserPlus, MoreVertical, MessageSquare, Check, X } from 'lucide-react';
import { motion } from 'framer-motion';
import { Button } from '../components/Button';
import { Input } from '../components/Input';
import styles from './Friends.module.css';

const MOCK_FRIENDS = [
  { id: 1, name: 'Alex Rivera', status: 'online', currentSong: 'Clair de Lune', avatar: 'A' },
  { id: 2, name: 'Maria Chen', status: 'offline', lastSeen: '2 hours ago', avatar: 'M' },
  { id: 3, name: 'James Wilson', status: 'practicing', currentSong: 'Für Elise', avatar: 'J' },
];

const MOCK_REQUESTS = [
  { id: 4, name: 'Sophie Taylor', mutual: 2, avatar: 'S' },
];

export function Friends() {
  const [activeTab, setActiveTab] = useState<'all' | 'requests'>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [friends, setFriends] = useState(MOCK_FRIENDS);
  const [requests, setRequests] = useState(MOCK_REQUESTS);

  const handleAcceptRequest = (id: number) => {
    const req = requests.find(r => r.id === id);
    if (req) {
      setRequests(requests.filter(r => r.id !== id));
      setFriends([...friends, { ...req, status: 'online', currentSong: '' }]);
      alert(`Accepted friend request from ${req.name}`);
    }
  };

  const handleDeclineRequest = (id: number) => {
    setRequests(requests.filter(r => r.id !== id));
  };

  const handleRemoveFriend = (id: number) => {
    if (confirm('Are you sure you want to remove this friend?')) {
      setFriends(friends.filter(f => f.id !== id));
    }
  };

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <div>
          <h1 className={styles.title}>Friends</h1>
          <p className={styles.subtitle}>Connect and practice with others.</p>
        </div>
        <Button variant="primary">
          <UserPlus size={16} style={{ marginRight: '8px' }} />
          Add Friend
        </Button>
      </header>

      <div className={styles.tabs}>
        <button 
          className={`${styles.tab} ${activeTab === 'all' ? styles.activeTab : ''}`}
          onClick={() => setActiveTab('all')}
        >
          All Friends ({friends.length})
        </button>
        <button 
          className={`${styles.tab} ${activeTab === 'requests' ? styles.activeTab : ''}`}
          onClick={() => setActiveTab('requests')}
        >
          Friend Requests {requests.length > 0 && <span className={styles.badge}>{requests.length}</span>}
        </button>
      </div>

      <div className={styles.content}>
        {activeTab === 'all' ? (
          <>
            <div className={styles.searchBar}>
              <Input 
                label=""
                placeholder="Search friends..." 
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            
            {friends.length === 0 ? (
              <div className={styles.emptyState}>
                <UserPlus size={48} color="var(--text-muted)" style={{ marginBottom: '16px' }} />
                <h3>No friends found</h3>
                <p>Try adjusting your search or add some new friends.</p>
              </div>
            ) : (
              <div className={styles.grid}>
                {friends.filter(f => f.name.toLowerCase().includes(searchQuery.toLowerCase())).map(friend => (
                  <motion.div key={friend.id} className={styles.card} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
                    <div className={styles.cardHeader}>
                      <div className={styles.avatar}>
                        {friend.avatar}
                        <div className={`${styles.statusDot} ${styles[friend.status]}`} />
                      </div>
                      <div className={styles.info}>
                        <h3 className={styles.name}>{friend.name}</h3>
                        <p className={styles.statusText}>
                          {friend.status === 'practicing' ? `Practicing ${friend.currentSong}` : 
                           friend.status === 'offline' ? `Last seen ${friend.lastSeen}` : 'Online'}
                        </p>
                      </div>
                      <button className={styles.iconBtn} onClick={() => handleRemoveFriend(friend.id)}>
                        <X size={16} />
                      </button>
                    </div>
                  </motion.div>
                ))}
              </div>
            )}
          </>
        ) : (
          <div className={styles.grid}>
            {requests.length === 0 ? (
              <div className={styles.emptyState}>
                <h3>No pending requests</h3>
              </div>
            ) : (
              requests.map(req => (
                <motion.div key={req.id} className={styles.card} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
                  <div className={styles.cardHeader}>
                    <div className={styles.avatar}>{req.avatar}</div>
                    <div className={styles.info}>
                      <h3 className={styles.name}>{req.name}</h3>
                      <p className={styles.statusText}>{req.mutual} mutual friends</p>
                    </div>
                  </div>
                  <div className={styles.actions}>
                    <Button variant="ghost" onClick={() => handleDeclineRequest(req.id)}>Decline</Button>
                    <Button variant="primary" onClick={() => handleAcceptRequest(req.id)}>Accept</Button>
                  </div>
                </motion.div>
              ))
            )}
          </div>
        )}
      </div>
    </div>
  );
}
