import { createContext, useContext, useState, useEffect } from 'react';
import type { ReactNode } from 'react';

export type AccountType = 'student' | 'teacher' | 'both';
export type ActiveRole = 'student' | 'teacher';

export interface UserProfile {
  firstName: string;
  lastName: string;
  email: string;
  avatarUrl?: string;
  joinedDate: string;
  accountType: AccountType | null;
  activeRole: ActiveRole | null;
  isOnboardingComplete: boolean;
  preferences: {
    pianoExperience: string;
    favoriteGenres: string[];
    dailyPracticeGoal: string;
    defaultInstrument: string;
    metronomeVolume: number;
  };
  privacy: {
    showPracticeTime: boolean;
    showStreak: boolean;
    showAchievements: boolean;
    showCurrentSong: boolean;
    appearOnLeaderboards: boolean;
    acceptFriendRequests: boolean;
  };
}

const defaultProfile: UserProfile = {
  firstName: '',
  lastName: '',
  email: '',
  joinedDate: new Date().toISOString(),
  accountType: null,
  activeRole: null,
  isOnboardingComplete: false,
  preferences: {
    pianoExperience: '',
    favoriteGenres: [],
    dailyPracticeGoal: '',
    defaultInstrument: 'Grand Piano',
    metronomeVolume: 80,
  },
  privacy: {
    showPracticeTime: true,
    showStreak: true,
    showAchievements: true,
    showCurrentSong: true,
    appearOnLeaderboards: true,
    acceptFriendRequests: true,
  }
};

interface UserContextType {
  profile: UserProfile;
  completedLessons: number;
  updateProfile: (updates: Partial<UserProfile>) => void;
  updatePreferences: (updates: Partial<UserProfile['preferences']>) => void;
  updatePrivacy: (updates: Partial<UserProfile['privacy']>) => void;
  completeOnboarding: (accountType: AccountType, preferences: UserProfile['preferences']) => void;
  incrementLessons: () => void;
  switchRole: (role: ActiveRole) => void;
  resetUser: () => void;
}

const UserContext = createContext<UserContextType | undefined>(undefined);

export function UserProvider({ children }: { children: ReactNode }) {
  const loadState = <T,>(key: string, defaultValue: T): T => {
    try {
      const stored = localStorage.getItem(`melodix_${key}`);
      return stored ? JSON.parse(stored) : defaultValue;
    } catch {
      return defaultValue;
    }
  };

  const [profile, setProfile] = useState<UserProfile>(() => {
    const saved = loadState<UserProfile | null>('profile', null);
    if (!saved) return defaultProfile;
    // Merge deeply to handle new schema fields if they didn't exist before
    return {
      ...defaultProfile,
      ...saved,
      preferences: { ...defaultProfile.preferences, ...saved.preferences },
      privacy: { ...defaultProfile.privacy, ...saved.privacy }
    };
  });
  
  const [completedLessons, setCompletedLessons] = useState<number>(() => loadState('completedLessons', 0));

  useEffect(() => {
    localStorage.setItem('melodix_profile', JSON.stringify(profile));
  }, [profile]);

  useEffect(() => {
    localStorage.setItem('melodix_completedLessons', JSON.stringify(completedLessons));
  }, [completedLessons]);

  const updateProfile = (updates: Partial<UserProfile>) => {
    setProfile(prev => ({ ...prev, ...updates }));
  };

  const updatePreferences = (updates: Partial<UserProfile['preferences']>) => {
    setProfile(prev => ({
      ...prev,
      preferences: { ...prev.preferences, ...updates }
    }));
  };

  const updatePrivacy = (updates: Partial<UserProfile['privacy']>) => {
    setProfile(prev => ({
      ...prev,
      privacy: { ...prev.privacy, ...updates }
    }));
  };

  const completeOnboarding = (type: AccountType, preferences: UserProfile['preferences']) => {
    updateProfile({
      accountType: type,
      activeRole: type === 'both' ? 'student' : type,
      isOnboardingComplete: true,
      preferences
    });
  };

  const incrementLessons = () => {
    setCompletedLessons(prev => prev + 1);
  };

  const switchRole = (role: ActiveRole) => {
    if (profile.accountType === 'both') {
      updateProfile({ activeRole: role });
    }
  };

  const resetUser = () => {
    setProfile(defaultProfile);
    setCompletedLessons(0);
    localStorage.removeItem('melodix_profile');
    localStorage.setItem('melodix_completedLessons', '0');
  };

  return (
    <UserContext.Provider 
      value={{ 
        profile, 
        completedLessons, 
        updateProfile,
        updatePreferences,
        updatePrivacy,
        completeOnboarding, 
        incrementLessons, 
        switchRole,
        resetUser
      }}
    >
      {children}
    </UserContext.Provider>
  );
}

export function useUser() {
  const context = useContext(UserContext);
  if (context === undefined) {
    throw new Error('useUser must be used within a UserProvider');
  }
  return context;
}
