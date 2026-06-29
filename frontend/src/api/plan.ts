import { apiClient } from './client';
import type { PlanRequest, WeekResponse } from '../types/api';

export const planApi = {
  nextSession: (payload: PlanRequest) =>
    apiClient.post<{ next_session: WeekResponse }>('/plan/next-session', payload),

  multiWeek: (payload: PlanRequest) =>
    apiClient.post<{ weeks: WeekResponse[] }>('/plan/multi-week', payload),
};
