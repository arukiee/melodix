import React, { useState } from 'react';
import { NavLink, useNavigate, useLocation } from 'react-router-dom';
import { Music, Home, Play, Compass, BarChart2, User, Users, FileText, ChevronDown, BookOpen, Layers, Search, Bell, Settings } from 'lucide-react';
import { useUser } from '../context/UserContext';
import { AccessibilityPanel } from './AccessibilityPanel';
import { MicMidiHUD } from './MicMidiHUD';
import styles from './Layout.module.css';

interface LayoutProps {
  children: React.ReactNode;
  role?: 'student' | 'teacher';
}

export function Layout({ children, role = 'student' }: LayoutProps) {
  const navigate = useNavigate();
  const location = useLocation();
  const { profile, switchRole } = useUser();
  const { accountType, activeRole } = profile;
  const [showRoleMenu, setShowRoleMenu] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);
  const [showAccessibility, setShowAccessibility] = useState(false);

  // Fallback to prop if activeRole is null
  const currentRole = activeRole || role;

  const studentLinks = [
    { name: 'Home', path: '/dashboard', icon: <Home size={20} /> },
    { name: 'Library', path: '/library', icon: <Music size={20} /> },
    { name: 'Practice', path: '/learn', icon: <Play size={20} /> },
    { name: 'Learn', path: '/learn', icon: <Compass size={20} /> },
    { name: 'Progress', path: '/progress', icon: <BarChart2 size={20} /> },
    { name: 'Friends', path: '/friends', icon: <Users size={20} /> },
    { name: 'Leaderboards', path: '/leaderboards', icon: <Layers size={20} /> },
    { name: 'Profile', path: '/profile', icon: <User size={20} /> },
  ];

  const teacherLinks = [
    { name: 'Dashboard', path: '/teacher', icon: <Home size={20} /> },
    { name: 'Students', path: '/teacher/students', icon: <Users size={20} /> },
    { name: 'Classes', path: '/teacher/classes', icon: <Layers size={20} /> },
    { name: 'Lessons', path: '/teacher/lessons', icon: <BookOpen size={20} /> },
    { name: 'Assignments', path: '/teacher/assignments', icon: <FileText size={20} /> },
    { name: 'Analytics', path: '/teacher/analytics', icon: <BarChart2 size={20} /> },
    { name: 'Profile', path: '/profile', icon: <User size={20} /> },
  ];

  const links = currentRole === 'student' ? studentLinks : teacherLinks;

  const isStudio = location.pathname.startsWith('/studio/') || location.pathname === '/processing' || location.pathname === '/onboarding';
  
  if (isStudio) {
    return <>{children}</>;
  }

  const handleRoleSwitch = (newRole: 'student' | 'teacher') => {
    switchRole(newRole);
    setShowRoleMenu(false);
    navigate(newRole === 'teacher' ? '/teacher' : '/dashboard');
  };

  return (
    <div className={styles.layout}>
      <aside className={styles.sidebar}>
        <div className={styles.brand} onClick={() => navigate('/')} style={{ cursor: 'pointer' }}>
          <Music size={28} color="var(--accent-primary)" />
          <span>Melodix</span>
        </div>
        
        <nav className={styles.nav}>
          {links.map((link) => (
            <NavLink
              key={link.name}
              to={link.path}
              className={({ isActive }) => 
                isActive ? `${styles.navItem} ${styles.active}` : styles.navItem
              }
            >
              {link.icon}
              {link.name}
            </NavLink>
          ))}
        </nav>

        <div className={styles.userSection}>
          {accountType === 'both' && (
            <div style={{ position: 'relative', marginBottom: '16px' }}>
              <div className={styles.roleSwitcherLabel}>Current Role</div>
              <button 
                className={styles.roleSwitcherBtn}
                onClick={() => setShowRoleMenu(!showRoleMenu)}
              >
                {currentRole === 'student' ? '🧑‍🎓 Student' : '👨‍🏫 Teacher'}
                <ChevronDown size={16} />
              </button>
              
              {showRoleMenu && (
                <div className={styles.roleMenu}>
                  <div 
                    className={`${styles.roleMenuItem} ${currentRole === 'student' ? styles.activeRole : ''}`}
                    onClick={() => handleRoleSwitch('student')}
                  >
                    🧑‍🎓 Student
                  </div>
                  <div 
                    className={`${styles.roleMenuItem} ${currentRole === 'teacher' ? styles.activeRole : ''}`}
                    onClick={() => handleRoleSwitch('teacher')}
                  >
                    👨‍🏫 Teacher
                  </div>
                </div>
              )}
            </div>
          )}

          {(() => {
            const displayName = profile.full_name?.trim() || `${profile.firstName || ''} ${profile.lastName || ''}`.trim() || profile.email?.split('@')[0] || 'Musician';
            const initials = displayName.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase() || 'M';
            return (
              <div className={styles.userCard} onClick={() => navigate('/profile')}>
                {profile.avatarUrl ? (
                  <img src={profile.avatarUrl} alt="Avatar" style={{ width: 36, height: 36, borderRadius: '50%', objectFit: 'cover' }} />
                ) : (
                  <div className={styles.avatar}>{initials}</div>
                )}
                <div className={styles.userInfo}>
                  <span className={styles.userName}>{displayName}</span>
                  <span className={styles.userRole}>
                    {accountType === 'both' ? 'Dual Account' : (currentRole === 'student' ? 'Student' : 'Instructor')}
                  </span>
                </div>
              </div>
            );
          })()}
        </div>
      </aside>
      
      <main className={styles.mainContent}>
        <header className={styles.topBar}>
          <div className={styles.searchContainer}>
            <Search size={18} className={styles.searchIcon} />
            <input type="text" placeholder="Search lessons, students, or classes..." className={styles.searchInput} />
          </div>
          
          <div className={styles.topActions}>
            <button className={styles.notificationBtn} onClick={() => setShowAccessibility(true)}>
              <Settings size={20} />
            </button>
            <button className={styles.notificationBtn} onClick={() => setShowNotifications(!showNotifications)}>
              <Bell size={20} />
              <span className={styles.notificationBadge}></span>
            </button>
            {showNotifications && (
              <div className={styles.notificationPopover}>
                <h4 className={styles.notificationTitle}>Notifications</h4>
                <div className={styles.notificationItem}>
                  <p><strong>Assignment due tomorrow</strong></p>
                  <span>Clair de Lune - Measure 15</span>
                </div>
                <div className={styles.notificationItem}>
                  <p><strong>New message from Instructor</strong></p>
                  <span>Great progress on your timing!</span>
                </div>
              </div>
            )}
          </div>
        </header>
        
        <div className={styles.pageContent}>
          {children}
        </div>
      </main>
      
      <AccessibilityPanel 
        isOpen={showAccessibility} 
        onClose={() => setShowAccessibility(false)} 
      />
      {currentRole === 'student' && <MicMidiHUD />}
    </div>
  );
}
