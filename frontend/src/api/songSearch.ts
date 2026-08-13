import { apiClient } from './client';

export interface SongMeta {
  id: string;
  title: string;
  artist: string;
  source: 'Local' | 'MIDI Repo' | 'MuseScore' | 'IMSLP' | 'Ultimate Guitar' | 'YouTube';
  difficulty?: 'easy' | 'medium' | 'hard';
  thumbnailUrl?: string;
  url?: string; // external url if any
}

export const songSearchApi = {
  searchSongs: async (query: string): Promise<SongMeta[]> => {
    try {
      const response = await apiClient.get('/songs/search', {
        params: { q: query }
      });
      return response.data;
    } catch (err) {
      console.error("Error searching songs, falling back to mock", err);
      // Fallback mock data if backend not ready
      return [
        {
          id: `yt_${Math.random()}`,
          title: `${query} (Piano Cover)`,
          artist: 'YouTube Creator',
          source: 'YouTube',
          difficulty: 'medium',
          thumbnailUrl: 'https://images.unsplash.com/photo-1552422535-c45813c61732?auto=format&fit=crop&w=300&q=80',
        },
        {
          id: `ug_${Math.random()}`,
          title: query,
          artist: 'Various',
          source: 'Ultimate Guitar',
          difficulty: 'easy',
        },
      ];
    }
  }
};
