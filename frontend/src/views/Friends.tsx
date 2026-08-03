import { useState, useEffect } from 'react';
import { UserPlus, X, Loader2 } from 'lucide-react';
import { motion } from 'framer-motion';
import { Button } from '../components/Button';
import { Input } from '../components/Input';
import { apiClient } from '../api/client';
import styles from './Friends.module.css';

interface Friend {
  id: string;
  user_id: string;
  friend_id: string;
  created_at: string;
  friend: {
    id: string;
    full_name: string;
    email: string;
    avatar_url?: string;
  };
}

interface FriendRequestItem {
  id: string;
  sender_id: string;
  receiver_id: string;
  status: string;
  created_at: string;
  sender: {
    id: string;
    full_name: string;
    email: string;
    avatar_url?: string;
  };
  receiver: {
    id: string;
    full_name: string;
    email: string;
    avatar_url?: string;
  };
}

interface UserSearchResult {
  id: string;
  full_name: string;
  email: string;
  avatar_url?: string;
}

export function Friends() {
  const [activeTab, setActiveTab] = useState<'all' | 'requests'>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [friends, setFriends] = useState<Friend[]>([]);
  const [incomingRequests, setIncomingRequests] = useState<FriendRequestItem[]>([]);
  const [outgoingRequests, setOutgoingRequests] = useState<FriendRequestItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Add Friend Modal State
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [userSearchTerm, setUserSearchTerm] = useState('');
  const [searchResults, setSearchResults] = useState<UserSearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [requestSentIds, setRequestSentIds] = useState<string[]>([]);

  const fetchSocialData = async () => {
    setIsLoading(true);
    try {
      const [friendsRes, reqsRes] = await Promise.all([
        apiClient.get('/social/friends'),
        apiClient.get('/social/friends/requests')
      ]);
      setFriends(friendsRes.data);
      setIncomingRequests(reqsRes.data.incoming || []);
      setOutgoingRequests(reqsRes.data.outgoing || []);
    } catch (err) {
      console.error('Failed to fetch social data:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchSocialData();
  }, []);

  // Search users for Add Friend Modal
  useEffect(() => {
    if (!userSearchTerm.trim()) {
      setSearchResults([]);
      return;
    }
    const timer = setTimeout(async () => {
      setIsSearching(true);
      try {
        const { data } = await apiClient.get(`/social/friends/search?q=${encodeURIComponent(userSearchTerm)}`);
        setSearchResults(data);
      } catch (err) {
        console.error('Failed to search users:', err);
      } finally {
        setIsSearching(false);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [userSearchTerm]);

  const handleSendRequest = async (targetUserId: string) => {
    try {
      await apiClient.post(`/social/friends/request/${targetUserId}`);
      setRequestSentIds(prev => [...prev, targetUserId]);
      fetchSocialData();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to send friend request');
    }
  };

  const handleAcceptRequest = async (requestId: string) => {
    try {
      await apiClient.post(`/social/friends/accept/${requestId}`);
      fetchSocialData();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to accept request');
    }
  };

  const handleDeclineRequest = async (requestId: string) => {
    try {
      await apiClient.post(`/social/friends/reject/${requestId}`);
      fetchSocialData();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to decline request');
    }
  };

  const handleCancelRequest = async (requestId: string) => {
    try {
      await apiClient.post(`/social/friends/cancel/${requestId}`);
      fetchSocialData();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to cancel request');
    }
  };

  const handleRemoveFriend = async (friendId: string) => {
    if (confirm('Are you sure you want to remove this friend?')) {
      try {
        await apiClient.delete(`/social/friends/${friendId}`);
        fetchSocialData();
      } catch (err: any) {
        alert(err.response?.data?.detail || 'Failed to remove friend');
      }
    }
  };

  const filteredFriends = friends.filter(f => 
    f.friend.full_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    f.friend.email.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <div>
          <h1 className={styles.title}>Friends</h1>
          <p className={styles.subtitle}>Connect and practice with active musicians.</p>
        </div>
        <Button variant="primary" onClick={() => setIsAddModalOpen(true)}>
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
          Friend Requests {incomingRequests.length > 0 && <span className={styles.badge}>{incomingRequests.length}</span>}
        </button>
      </div>

      <div className={styles.content}>
        {isLoading ? (
          <div className={styles.emptyState}>
            <Loader2 size={32} className="spin" color="var(--accent-primary)" />
            <p style={{ marginTop: '12px' }}>Loading friends...</p>
          </div>
        ) : activeTab === 'all' ? (
          <>
            <div className={styles.searchBar}>
              <Input 
                label=""
                placeholder="Search friends by name or email..." 
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            
            {filteredFriends.length === 0 ? (
              <div className={styles.emptyState}>
                <UserPlus size={48} color="var(--text-muted)" style={{ marginBottom: '16px' }} />
                <h3>No friends found</h3>
                <p>Use "Add Friend" to search and connect with other users.</p>
              </div>
            ) : (
              <div className={styles.grid}>
                {filteredFriends.map(f => {
                  const name = f.friend.full_name || f.friend.email;
                  const initial = name.charAt(0).toUpperCase();
                  return (
                    <motion.div key={f.id} className={styles.card} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
                      <div className={styles.cardHeader}>
                        {f.friend.avatar_url ? (
                          <img src={f.friend.avatar_url} alt={name} className={styles.avatar} style={{ objectFit: 'cover' }} />
                        ) : (
                          <div className={styles.avatar}>{initial}</div>
                        )}
                        <div className={styles.info}>
                          <h3 className={styles.name}>{name}</h3>
                          <p className={styles.statusText}>{f.friend.email}</p>
                        </div>
                        <button className={styles.iconBtn} onClick={() => handleRemoveFriend(f.friend_id)}>
                          <X size={16} />
                        </button>
                      </div>
                    </motion.div>
                  );
                })}
              </div>
            )}
          </>
        ) : (
          <div>
            <h3 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '16px' }}>Incoming Requests ({incomingRequests.length})</h3>
            {incomingRequests.length === 0 ? (
              <div className={styles.emptyState} style={{ padding: '24px' }}>
                <p>No incoming friend requests.</p>
              </div>
            ) : (
              <div className={styles.grid} style={{ marginBottom: '32px' }}>
                {incomingRequests.map(req => {
                  const senderName = req.sender.full_name || req.sender.email;
                  const initial = senderName.charAt(0).toUpperCase();
                  return (
                    <motion.div key={req.id} className={styles.card} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
                      <div className={styles.cardHeader}>
                        <div className={styles.avatar}>{initial}</div>
                        <div className={styles.info}>
                          <h3 className={styles.name}>{senderName}</h3>
                          <p className={styles.statusText}>{req.sender.email}</p>
                        </div>
                      </div>
                      <div className={styles.actions}>
                        <Button variant="ghost" onClick={() => handleDeclineRequest(req.id)}>Decline</Button>
                        <Button variant="primary" onClick={() => handleAcceptRequest(req.id)}>Accept</Button>
                      </div>
                    </motion.div>
                  );
                })}
              </div>
            )}

            {outgoingRequests.length > 0 && (
              <>
                <h3 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '16px' }}>Outgoing Requests ({outgoingRequests.length})</h3>
                <div className={styles.grid}>
                  {outgoingRequests.map(req => {
                    const receiverName = req.receiver.full_name || req.receiver.email;
                    const initial = receiverName.charAt(0).toUpperCase();
                    return (
                      <motion.div key={req.id} className={styles.card} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
                        <div className={styles.cardHeader}>
                          <div className={styles.avatar}>{initial}</div>
                          <div className={styles.info}>
                            <h3 className={styles.name}>{receiverName}</h3>
                            <p className={styles.statusText}>Pending confirmation</p>
                          </div>
                        </div>
                        <div className={styles.actions}>
                          <Button variant="ghost" onClick={() => handleCancelRequest(req.id)}>Cancel Request</Button>
                        </div>
                      </motion.div>
                    );
                  })}
                </div>
              </>
            )}
          </div>
        )}
      </div>

      {/* Add Friend Modal */}
      {isAddModalOpen && (
        <div style={{
          position: 'fixed', inset: 0, zIndex: 1000,
          background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(4px)',
          display: 'flex', alignItems: 'center', justifyContent: 'center'
        }}>
          <motion.div 
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            style={{
              background: 'var(--bg-elevated)', border: '1px solid var(--border-color)',
              borderRadius: '16px', width: '90%', maxWidth: '480px', padding: '24px'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h2 style={{ fontSize: '20px', fontWeight: 600 }}>Add Friend</h2>
              <button onClick={() => setIsAddModalOpen(false)} style={{ background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer' }}>
                <X size={20} />
              </button>
            </div>

            <Input 
              label=""
              placeholder="Search by name or email..."
              value={userSearchTerm}
              onChange={(e) => setUserSearchTerm(e.target.value)}
            />

            <div style={{ marginTop: '16px', maxHeight: '280px', overflowY: 'auto' }}>
              {isSearching ? (
                <div style={{ textAlign: 'center', padding: '24px' }}>
                  <Loader2 size={24} className="spin" color="var(--accent-primary)" />
                </div>
              ) : searchResults.length === 0 ? (
                userSearchTerm.trim() ? (
                  <p style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '16px' }}>No users found matching "{userSearchTerm}"</p>
                ) : (
                  <p style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '16px' }}>Type a name or email to search active musicians.</p>
                )
              ) : (
                searchResults.map(user => {
                  const isSent = requestSentIds.includes(user.id);
                  const initial = user.full_name.charAt(0).toUpperCase();
                  return (
                    <div key={user.id} style={{
                      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                      padding: '12px', borderBottom: '1px solid var(--border-color)'
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                        <div className={styles.avatar}>{initial}</div>
                        <div>
                          <div style={{ fontWeight: 600 }}>{user.full_name}</div>
                          <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{user.email}</div>
                        </div>
                      </div>
                      <Button 
                        variant={isSent ? "ghost" : "primary"} 
                        disabled={isSent}
                        onClick={() => handleSendRequest(user.id)}
                        style={{ fontSize: '13px', padding: '6px 12px' }}
                      >
                        {isSent ? 'Sent' : 'Add'}
                      </Button>
                    </div>
                  );
                })
              )}
            </div>
          </motion.div>
        </div>
      )}
    </div>
  );
}
