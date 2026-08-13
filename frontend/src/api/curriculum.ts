import { apiClient } from './client';

export interface CheckpointSchema {
  id: string;
  title: string;
  pass_threshold_percentage: number;
  unlocks_module_id?: string;
}

export interface ModuleSchema {
  id: string;
  title: string;
  slug: string;
  description?: string;
  display_order: number;
  is_unlocked_by_default: boolean;
  checkpoint?: CheckpointSchema;
}

export interface LearningPathSchema {
  id: string;
  title: string;
  slug: string;
  description?: string;
  target_role: string;
  display_order: number;
  modules: ModuleSchema[];
}

export const curriculumApi = {
  getLearningPaths: async (): Promise<LearningPathSchema[]> => {
    const response = await apiClient.get<LearningPathSchema[]>('/api/v1/curriculum/paths');
    return response.data;
  },
  getLearningPath: async (idOrSlug: string): Promise<LearningPathSchema> => {
    const response = await apiClient.get<LearningPathSchema>(`/api/v1/curriculum/paths/${idOrSlug}`);
    return response.data;
  },
};
