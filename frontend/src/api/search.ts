import { apiClient } from './client';

export interface SearchResult {
  id: string;
  title: string;
  artist: string;
  provider: string;
  difficulty: string;
  hasMidi: boolean;
  hasChords: boolean;
  hasSheetMusic: boolean;
  duration?: number;
  popularity: number;
  thumbnailUrl?: string;
  rank_score: number;
}

export interface ImportCommitResponse {
  success: boolean;
  song_id?: string;
  message: string;
}

export const searchApi = {
  searchSongs: async (query: string, filters: Record<string, any> = {}): Promise<SearchResult[]> => {
    const params = new URLSearchParams();
    params.append('q', query);
    for (const [key, value] of Object.entries(filters)) {
      if (value !== undefined && value !== null) {
        params.append(key, String(value));
      }
    }
    const response = await apiClient.get<SearchResult[]>(`/songs/search?${params.toString()}`);
    return response.data;
  },

  importFromSearch: async (result: SearchResult): Promise<ImportCommitResponse> => {
    const response = await apiClient.post<ImportCommitResponse>('/songs/import_from_search', {
      id: result.id,
      title: result.title,
      artist: result.artist,
      provider: result.provider
    });
    return response.data;
  }
};
