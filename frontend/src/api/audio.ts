import { apiClient } from './client';

export interface ProcessingJobStatus {
  id: string;
  song_id?: string;
  status: string;
  progress_percent: number;
  error_message?: string | null;
  stage_log: Array<{
    stage: string;
    started_at: string;
    completed_at?: string;
    result?: string;
    error?: string;
  }>;
}

export interface ProcessingJobSummary {
  id: string;
  status: string;
  progress_percent: number;
  pipeline_version: string;
  created_at?: string;
}

export async function getSongById(songId: string): Promise<{ id: string; title: string; composer?: string; artist?: string }> {
  const { data } = await apiClient.get(`/songs/${songId}`);
  return data;
}

export async function uploadAudio(file: File, songId?: string): Promise<{ audio_asset_id: string; processing_job_id: string }> {
  const formData = new FormData();
  formData.append('file', file);
  if (songId) {
    formData.append('song_id', songId);
  }

  try {
    const { data } = await apiClient.post('/api/v1/audio/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    return data;
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || 'Upload failed');
  }
}

export async function getPipelineStatus(jobId: string): Promise<ProcessingJobStatus> {
  const { data } = await apiClient.get<ProcessingJobStatus>(`/api/v1/pipeline/${jobId}`);
  return data;
}

export async function getUserPipelineJobs(): Promise<ProcessingJobSummary[]> {
  const { data } = await apiClient.get<ProcessingJobSummary[]>('/api/v1/pipeline/user/jobs');
  return data;
}

export async function getPipelineNotes(jobId: string) {
  const { data } = await apiClient.get(`/api/v1/pipeline/${jobId}/notes`);
  return data;
}

export async function getPipelineCurriculum(jobId: string) {
  const { data } = await apiClient.get(`/api/v1/pipeline/${jobId}/curriculum`);
  return data;
}

export async function importSong(songId: string): Promise<any> {
  try {
    const { data } = await apiClient.post('/api/v1/pipeline/import-song', { song_id: songId });
    return data;
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || 'Failed to import song. No valid source found.');
  }
}
