import { apiClient } from './client';
import type {
  AnalyzeStartRequest,
  AnalyzeStartResponse,
  AnalyzeCoachRequest,
  AnalyzeCoachResponse,
} from '../types/api';

export const analyzeApi = {
  start: (payload: AnalyzeStartRequest) =>
    apiClient.post<AnalyzeStartResponse>('/analyze/start', payload),

  coach: (payload: AnalyzeCoachRequest) =>
    apiClient.post<AnalyzeCoachResponse>('/analyze/coach', payload),
};
