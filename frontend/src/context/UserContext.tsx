import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { apiClient } from '../api/client';

export type AccountType = 'student' | 'teacher' | 'both';
export type ActiveRole = 'student' | 'teacher' | 'admin';

export interface UserProfile {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  full_name?: string;
  avatarUrl?: string;
  joinedDate: string;
  accountType: AccountType | null;
  activeRole: ActiveRole | null;
  isOnboardingComplete: boolean;
  role: string;
  authProvider: string;
  bio: string;
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
  id: '',
  email: '',
  firstName: '',
  lastName: '',
  joinedDate: new Date().toISOString(),
  accountType: null,
  activeRole: null,
  isOnboardingComplete: false,
  role: 'STUDENT',
  authProvider: 'EMAIL',
  bio: '',
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
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (accessToken: string, refreshToken: string) => Promise<void>;
  logout: () => void;
  updateProfile: (updates: Partial<UserProfile>) => void;
  updatePreferences: (updates: Partial<UserProfile['preferences']>) => void;
  updatePrivacy: (updates: Partial<UserProfile['privacy']>) => void;
  saveUserInfo: (fullName: string, avatarUrl?: string) => Promise<void>;
  saveProfile: (updates: Record<string, unknown>) => Promise<void>;
  completeOnboarding: (accountType: AccountType, preferences: UserProfile['preferences']) => void;
  switchRole: (role: ActiveRole) => void;
  refreshUser: () => Promise<void>;
}

const UserContext = createContext<UserContextType | undefined>(undefined);

export function UserProvider({ children }: { children: ReactNode }) {
  const [profile, setProfile] = useState<UserProfile>(defaultProfile);
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const fetchUser = async () => {
    try {
      const { data } = await apiClient.get('/users/me');
      // Also fetch profile details
      let profileData = null;
      try {
        const profileRes = await apiClient.get('/users/profile');
        profileData = profileRes.data;
      } catch { /* profile may not exist yet */ }

      setProfile(prev => ({
        ...prev,
        id: data.id,
        email: data.email,
        firstName: data.full_name?.split(' ')[0] || '',
        lastName: data.full_name?.split(' ').slice(1).join(' ') || '',
        full_name: data.full_name,
        avatarUrl: data.avatar_url,
        role: data.role,
        authProvider: data.auth_provider || 'EMAIL',
        activeRole: data.role.toLowerCase() as ActiveRole,
        isOnboardingComplete: data.onboarding_completed,
        bio: profileData?.bio || '',
        preferences: profileData ? {
          ...prev.preferences,
          pianoExperience: profileData.skill_level || prev.preferences.pianoExperience,
          favoriteGenres: profileData.preferred_genres || prev.preferences.favoriteGenres,
          dailyPracticeGoal: profileData.daily_practice_goal?.toString() || prev.preferences.dailyPracticeGoal,
          defaultInstrument: profileData.preferred_instrument || prev.preferences.defaultInstrument,
        } : prev.preferences,
      }));
      setIsAuthenticated(true);
    } catch (error) {
      console.error('Failed to fetch user:', error);
      logout();
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      fetchUser();
    } else {
      setIsLoading(false);
    }
  }, []);

  const login = async (accessToken: string, refreshToken: string) => {
    localStorage.setItem('access_token', accessToken);
    localStorage.setItem('refresh_token', refreshToken);
    setIsLoading(true);
    await fetchUser();
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setProfile(defaultProfile);
    setIsAuthenticated(false);
  };

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

  const saveUserInfo = async (fullName: string, avatarUrl?: string) => {
    const payload: Record<string, string> = { full_name: fullName };
    if (avatarUrl !== undefined) payload.avatar_url = avatarUrl;
    await apiClient.patch('/users/me', payload);
    setProfile(prev => ({
      ...prev,
      full_name: fullName,
      firstName: fullName.split(' ')[0] || '',
      lastName: fullName.split(' ').slice(1).join(' ') || '',
      ...(avatarUrl !== undefined ? { avatarUrl } : {}),
    }));
  };

  const saveProfile = async (updates: Record<string, unknown>) => {
    const { data } = await apiClient.patch('/users/profile', updates);
    setProfile(prev => ({
      ...prev,
      preferences: {
        ...prev.preferences,
        pianoExperience: data.skill_level || prev.preferences.pianoExperience,
        favoriteGenres: data.preferred_genres || prev.preferences.favoriteGenres,
        dailyPracticeGoal: data.daily_practice_goal?.toString() || prev.preferences.dailyPracticeGoal,
        defaultInstrument: data.preferred_instrument || prev.preferences.defaultInstrument,
      },
    }));
  };

  const completeOnboarding = async (type: AccountType, preferences: UserProfile['preferences']) => {
    try {
      await apiClient.post('/users/complete-onboarding', {
        skill_level: preferences.pianoExperience,
        preferred_instrument: preferences.defaultInstrument,
        daily_practice_goal: parseInt(preferences.dailyPracticeGoal) || 30,
        preferred_genres: preferences.favoriteGenres,
      });
      updateProfile({
        accountType: type,
        activeRole: type === 'both' ? 'student' : type as ActiveRole,
        isOnboardingComplete: true,
        preferences
      });
    } catch (error) {
      console.error('Failed to complete onboarding:', error);
    }
  };

  const refreshUser = async () => {
    await fetchUser();
  };

  const switchRole = (role: ActiveRole) => {
    if (profile.accountType === 'both' || profile.role === 'ADMIN') {
      updateProfile({ activeRole: role });
    }
  };

  return (
    <UserContext.Provider 
      value={{ 
        profile, 
        isAuthenticated,
        isLoading,
        login,
        logout,
        updateProfile,
        updatePreferences,
        updatePrivacy,
        saveUserInfo,
        saveProfile,
        completeOnboarding, 
        switchRole,
        refreshUser
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
