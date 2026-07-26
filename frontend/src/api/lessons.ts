import { apiClient } from './client';

export interface LessonObjective {
  id: string;
  title: string;
  description: string;
}

export interface Lesson {
  id: string;
  teacher_id: string;
  title: string;
  slug: string;
  description?: string;
  category?: string;
  difficulty?: 'BEGINNER' | 'INTERMEDIATE' | 'ADVANCED';
  genre?: string;
  estimated_duration?: number;
  display_order: number;
  thumbnail_url?: string;
  objectives: LessonObjective[];
  visibility: 'PUBLIC' | 'PRIVATE';
  is_published: boolean;
  published_at?: string;
  created_at: string;
  updated_at: string;
}

export interface LessonListResponse {
  items: Lesson[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface LessonCreate {
  title: string;
  description?: string;
  category?: string;
  difficulty?: 'BEGINNER' | 'INTERMEDIATE' | 'ADVANCED';
  genre?: string;
  estimated_duration?: number;
  thumbnail_url?: string;
  objectives?: LessonObjective[];
  visibility?: 'PUBLIC' | 'PRIVATE';
  is_published?: boolean;
}

export interface LessonUpdate extends Partial<LessonCreate> {}

export const lessonsApi = {
  getLessons: async (params?: {
    search?: string;
    category?: string;
    difficulty?: string;
    page?: number;
    size?: number;
  }) => {
    const response = await apiClient.get<LessonListResponse>('/lessons', { params });
    return response.data;
  },

  getTeacherLessons: async (params?: { page?: number; size?: number }) => {
    const response = await apiClient.get<LessonListResponse>('/lessons/teachers/me/lessons', { params });
    return response.data;
  },

  getLesson: async (idOrSlug: string) => {
    const response = await apiClient.get<Lesson>(`/lessons/${idOrSlug}`);
    return response.data;
  },

  createLesson: async (data: LessonCreate) => {
    const response = await apiClient.post<Lesson>('/lessons', data);
    return response.data;
  },

  updateLesson: async (id: string, data: LessonUpdate) => {
    const response = await apiClient.patch<Lesson>(`/lessons/${id}`, data);
    return response.data;
  },

  deleteLesson: async (id: string) => {
    await apiClient.delete(`/lessons/${id}`);
  }
};
