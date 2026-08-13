import { apiClient } from './client';

export interface Instrument {
  id: string;
  name: string;
}

export const instrumentsApi = {
  getInstruments: async (): Promise<Instrument[]> => {
    const response = await apiClient.get<Instrument[]>('/instruments');
    return response.data;
  }
};
