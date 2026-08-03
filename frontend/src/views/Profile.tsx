
import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { User, Settings, Shield, Bell, Check, Edit2, LogOut, Trash2, Camera, Link as LinkIcon, Music, Activity } from 'lucide-react';
import { motion } from 'framer-motion';
import { Button } from '../components/Button';
import { Input } from '../components/Input';
import { Toggle } from '../components/Toggle';
import { useUser } from '../context/UserContext';
import styles from './Profile.module.css';

export function Profile() {
  const { profile, updateProfile, updatePreferences, updatePrivacy, saveUserInfo, saveProfile, logout } = useUser();
  const navigate = useNavigate();
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const [editForm, setEditForm] = useState({
    firstName: profile.firstName || profile.full_name?.split(' ')[0] || '',
    lastName: profile.lastName || profile.full_name?.split(' ').slice(1).join(' ') || '',
    email: profile.email || '',
  });

  useEffect(() => {
    setEditForm({
      firstName: profile.firstName || profile.full_name?.split(' ')[0] || '',
      lastName: profile.lastName || profile.full_name?.split(' ').slice(1).join(' ') || '',
      email: profile.email || '',
    });
  }, [profile.firstName, profile.lastName, profile.full_name, profile.email]);

  const displayName = profile.full_name?.trim() || `${profile.firstName || ''} ${profile.lastName || ''}`.trim() || profile.email?.split('@')[0] || 'User';

  const handleAvatarClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = async (event) => {
        const newAvatarUrl = event.target?.result as string;
        try {
          await saveUserInfo(displayName, newAvatarUrl);
        } catch {
          updateProfile({ avatarUrl: newAvatarUrl });
        }
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      const fullName = `${editForm.firstName} ${editForm.lastName}`.trim();
      await saveUserInfo(fullName);
      await saveProfile({
        skill_level: profile.preferences.pianoExperience || undefined,
        preferred_instrument: profile.preferences.defaultInstrument || undefined,
        daily_practice_goal: parseInt(profile.preferences.dailyPracticeGoal) || undefined,
        preferred_genres: profile.preferences.favoriteGenres.length ? profile.preferences.favoriteGenres : undefined,
      });
      setIsEditing(false);
    } catch (error) {
      console.error('Failed to save profile:', error);
      alert('Failed to save changes. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  const handleSignOut = () => {
    logout();
    navigate('/login');
  };

  const handleResetProgress = () => {
    if (confirm("Are you sure you want to reset all learning progress? This cannot be undone.")) {
      alert("Progress reset simulated.");
    }
  };

  const handleDeleteAccount = () => {
    if (confirm("Are you sure you want to permanently delete your account? This cannot be undone.")) {
      logout();
      window.location.href = '/login';
    }
  };

  const getInitials = () => {
    return displayName.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase() || 'U';
  };

  const displayRole = profile.accountType === 'both' ? 'Dual Account (Student & Teacher)' : 
                     (profile.accountType === 'teacher' ? 'Teacher' : 'Student');

  return (
    <motion.div 
      className={styles.container}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <header className={styles.header}>
        <div className={styles.avatarWrapper} onClick={handleAvatarClick}>
          {profile.avatarUrl ? (
            <img src={profile.avatarUrl} alt="Avatar" style={{ width: '100%', height: '100%', borderRadius: '50%', objectFit: 'cover', border: '1px solid var(--border-color)' }} />
          ) : (
            <div className={styles.avatarGradient}>
              {getInitials()}
            </div>
          )}
          <div className={styles.avatarHover}>
            <Camera size={20} />
            <span>Change</span>
          </div>
          <input 
            type="file" 
            ref={fileInputRef} 
            onChange={handleFileChange} 
            accept="image/*" 
            style={{ display: 'none' }} 
          />
        </div>
        <div className={styles.userInfo}>
          <h1 className={styles.name}>{displayName}</h1>
          <div className={styles.roleBadge}>{displayRole}</div>
          <p className={styles.email}>{profile.email}</p>
        </div>
        <div style={{ marginLeft: 'auto' }}>
          {!isEditing ? (
            <Button variant="secondary" onClick={() => setIsEditing(true)}>
              <Edit2 size={16} style={{ marginRight: '8px' }} />
              Edit Profile
            </Button>
          ) : (
            <div style={{ display: 'flex', gap: '12px' }}>
              <Button variant="ghost" onClick={() => setIsEditing(false)}>Cancel</Button>
              <Button variant="primary" onClick={handleSave} disabled={isSaving}>
                <Check size={16} style={{ marginRight: '8px' }} />
                {isSaving ? 'Saving...' : 'Save Changes'}
              </Button>
            </div>
          )}
        </div>
      </header>

      {/* 1. Personal Information */}
      <section className={styles.section}>
        <div className={styles.sectionHeader}>
          <h2 className={styles.sectionTitle}>
            <User size={20} color="var(--accent-primary)" />
            Personal Information
          </h2>
          <p className={styles.sectionDesc}>Update your personal details and identity.</p>
        </div>
        
        {isEditing ? (
          <div className={styles.formGrid}>
            <Input label="First Name" value={editForm.firstName} onChange={e => setEditForm({...editForm, firstName: e.target.value})} />
            <Input label="Last Name" value={editForm.lastName} onChange={e => setEditForm({...editForm, lastName: e.target.value})} />
            <Input label="Email" type="email" value={editForm.email} onChange={e => setEditForm({...editForm, email: e.target.value})} />
          </div>
        ) : (
          <div className={styles.infoGrid}>
            <div className={styles.infoBlock}>
              <span className={styles.infoLabel}>First Name</span>
              <span className={styles.infoValue}>{profile.firstName || 'Not set'}</span>
            </div>
            <div className={styles.infoBlock}>
              <span className={styles.infoLabel}>Last Name</span>
              <span className={styles.infoValue}>{profile.lastName || 'Not set'}</span>
            </div>
            <div className={styles.infoBlock}>
              <span className={styles.infoLabel}>Email</span>
              <span className={styles.infoValue}>{profile.email || 'Not set'}</span>
            </div>
          </div>
        )}
      </section>

      {/* 2. Account Settings */}
      <section className={styles.section}>
        <div className={styles.sectionHeader}>
          <h2 className={styles.sectionTitle}>
            <Settings size={20} color="var(--accent-primary)" />
            Account Settings
          </h2>
          <p className={styles.sectionDesc}>Manage your account type and status.</p>
        </div>
        <div className={styles.infoGrid}>
          <div className={styles.infoBlock}>
            <span className={styles.infoLabel}>Account Type</span>
            <span className={styles.infoValue}>{displayRole}</span>
          </div>
          <div className={styles.infoBlock}>
            <span className={styles.infoLabel}>Joined Date</span>
            <span className={styles.infoValue}>{new Date(profile.joinedDate).toLocaleDateString()}</span>
          </div>
          <div className={styles.infoBlock}>
            <span className={styles.infoLabel}>Status</span>
            <span className={styles.infoValue} style={{ color: 'var(--status-success)' }}>Active</span>
          </div>
        </div>
      </section>

      {/* 3. Connected Accounts */}
      <section className={styles.section}>
        <div className={styles.sectionHeader}>
          <h2 className={styles.sectionTitle}>
            <LinkIcon size={20} color="var(--accent-primary)" />
            Connected Accounts
          </h2>
          <p className={styles.sectionDesc}>Manage third-party authentication providers.</p>
        </div>
        <div className={styles.accountBox}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <div style={{ width: '40px', height: '40px', background: '#FFF', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#000', fontWeight: 'bold' }}>G</div>
            <div>
              <div style={{ fontWeight: 500, color: 'var(--text-primary)' }}>Google</div>
              <div style={{ fontSize: 'var(--text-caption)', color: 'var(--text-secondary)' }}>{profile.authProvider === 'GOOGLE' ? profile.email : 'Not connected'}</div>
            </div>
          </div>
          {profile.authProvider === 'GOOGLE' ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--status-success)', fontSize: 'var(--text-label)', fontWeight: 500 }}>
              <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--status-success)' }} />
              Connected
            </div>
          ) : (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-muted)', fontSize: 'var(--text-label)', fontWeight: 500 }}>
              <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--text-muted)' }} />
              Not linked
            </div>
          )}
        </div>
      </section>

      {/* 4. Preferences */}
      <section className={styles.section}>
        <div className={styles.sectionHeader}>
          <h2 className={styles.sectionTitle}>
            <Music size={20} color="var(--accent-primary)" />
            Learning Preferences
          </h2>
          <p className={styles.sectionDesc}>Customize your practice experience and playback settings.</p>
        </div>
        
        <div style={{ marginBottom: '32px' }}>
          <h3 style={{ fontSize: '14px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '16px' }}>Practice Experience</h3>
          {isEditing ? (
            <div className={styles.formGrid}>
              <Input label="Piano Experience" value={profile.preferences.pianoExperience} onChange={e => updatePreferences({ pianoExperience: e.target.value })} />
              <Input label="Daily Goal" value={profile.preferences.dailyPracticeGoal} onChange={e => updatePreferences({ dailyPracticeGoal: e.target.value })} />
              <Input label="Instrument" value={profile.preferences.defaultInstrument} onChange={e => updatePreferences({ defaultInstrument: e.target.value })} />
            </div>
          ) : (
            <div className={styles.infoGrid}>
              <div className={styles.infoBlock}>
                <span className={styles.infoLabel}>Piano Experience</span>
                <span className={styles.infoValue}>{profile.preferences.pianoExperience || 'Not set'}</span>
              </div>
              <div className={styles.infoBlock}>
                <span className={styles.infoLabel}>Daily Goal</span>
                <span className={styles.infoValue}>{profile.preferences.dailyPracticeGoal || 'Not set'}</span>
              </div>
              <div className={styles.infoBlock}>
                <span className={styles.infoLabel}>Default Instrument</span>
                <span className={styles.infoValue}>{profile.preferences.defaultInstrument || 'Grand Piano'}</span>
              </div>
            </div>
          )}
        </div>

        <div>
          <h3 style={{ fontSize: '14px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '16px' }}>Playback</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div className={styles.infoBlock}>
                <span className={styles.infoLabel}>Metronome Volume</span>
                <span className={styles.infoValue}>{profile.preferences.metronomeVolume}%</span>
              </div>
              {isEditing && (
                <input 
                  type="range" 
                  min="0" 
                  max="100" 
                  value={profile.preferences.metronomeVolume} 
                  onChange={e => updatePreferences({ metronomeVolume: parseInt(e.target.value) })}
                  style={{ width: '150px' }}
                />
              )}
            </div>
          </div>
        </div>
      </section>

      {/* 5. Privacy */}
      <section className={styles.section}>
        <div className={styles.sectionHeader}>
          <h2 className={styles.sectionTitle}>
            <Shield size={20} color="var(--accent-primary)" />
            Privacy
          </h2>
          <p className={styles.sectionDesc}>Control your visibility and social features.</p>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <Toggle 
            label="Show Practice Time" 
            description="Allow friends and teachers to see your total practice hours."
            checked={profile.privacy.showPracticeTime}
            onChange={(checked) => updatePrivacy({ showPracticeTime: checked })}
          />
          <Toggle 
            label="Show Streak" 
            description="Display your current daily streak on your public profile."
            checked={profile.privacy.showStreak}
            onChange={(checked) => updatePrivacy({ showStreak: checked })}
          />
          <Toggle 
            label="Appear on Leaderboards" 
            description="Include your stats in weekly global and class leaderboards."
            checked={profile.privacy.appearOnLeaderboards}
            onChange={(checked) => updatePrivacy({ appearOnLeaderboards: checked })}
          />
          <Toggle 
            label="Accept Friend Requests" 
            description="Allow other students to send you friend requests."
            checked={profile.privacy.acceptFriendRequests}
            onChange={(checked) => updatePrivacy({ acceptFriendRequests: checked })}
          />
        </div>
      </section>

      {/* 6. Notifications */}
      <section className={styles.section}>
        <div className={styles.sectionHeader}>
          <h2 className={styles.sectionTitle}>
            <Bell size={20} color="var(--accent-primary)" />
            Notifications
          </h2>
          <p className={styles.sectionDesc}>Manage how and when we contact you.</p>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <Toggle 
            label="Practice Reminders" 
            description="Get notified if you haven't met your daily practice goal."
            checked={true}
            onChange={() => {}}
          />
          <Toggle 
            label="Assignment Updates" 
            description="Receive alerts when your teacher assigns new material."
            checked={true}
            onChange={() => {}}
          />
          <Toggle 
            label="Teacher Feedback" 
            description="Get notified when your teacher reviews your performance."
            checked={true}
            onChange={() => {}}
          />
        </div>
      </section>

      {/* 7. Danger Zone */}
      <section className={styles.section} style={{ borderColor: 'rgba(239, 68, 68, 0.2)' }}>
        <div className={styles.sectionHeader}>
          <h2 className={styles.sectionTitle} style={{ color: 'var(--status-error)' }}>
            Danger Zone
          </h2>
          <p className={styles.sectionDesc}>Destructive actions for your account.</p>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div className={styles.dangerBox}>
            <div>
              <div style={{ fontWeight: 500, color: 'var(--text-primary)' }}>Sign Out</div>
              <div style={{ fontSize: 'var(--text-caption)', color: 'var(--text-secondary)' }}>Log out of this device.</div>
            </div>
            <Button variant="secondary" onClick={handleSignOut}>
              <LogOut size={16} style={{ marginRight: '8px' }} />
              Sign Out
            </Button>
          </div>
          <div className={styles.dangerBox}>
            <div>
              <div style={{ fontWeight: 500, color: 'var(--text-primary)' }}>Reset Progress</div>
              <div style={{ fontSize: 'var(--text-caption)', color: 'var(--text-secondary)' }}>Clear all learning history and AI assessment data.</div>
            </div>
            <Button variant="secondary" onClick={handleResetProgress} style={{ color: 'var(--status-error)', borderColor: 'rgba(239, 68, 68, 0.2)' }}>
              <Activity size={16} style={{ marginRight: '8px' }} />
              Reset Data
            </Button>
          </div>
          <div className={styles.dangerBox}>
            <div>
              <div style={{ fontWeight: 500, color: 'var(--text-primary)' }}>Delete Account</div>
              <div style={{ fontSize: 'var(--text-caption)', color: 'var(--text-secondary)' }}>Permanently delete your account and all data.</div>
            </div>
            <Button variant="primary" onClick={handleDeleteAccount} style={{ background: 'var(--status-error)', color: '#FFF' }}>
              <Trash2 size={16} style={{ marginRight: '8px' }} />
              Delete Account
            </Button>
          </div>
        </div>
      </section>

    </motion.div>
  );
}
