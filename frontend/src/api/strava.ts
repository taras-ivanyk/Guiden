import { apiClient } from './client';
import type { ActivitySummary, RecentSummary } from '../types/api';

function todayStr(): string {
  return new Date().toISOString().slice(0, 10);
}
function weeksAgoStr(n: number): string {
  const d = new Date();
  d.setDate(d.getDate() - n * 7);
  return d.toISOString().slice(0, 10);
}

export const stravaApi = {
  getActivities: (weeks = 8) =>
    apiClient.get<ActivitySummary[]>(
      `/strava/activities?start=${weeksAgoStr(weeks)}&end=${todayStr()}`,
    ),
  getActivitiesRange: (start: string, end: string) =>
    apiClient.get<ActivitySummary[]>(`/strava/activities?start=${start}&end=${end}`),
  getActivity: (id: string) => apiClient.get<ActivitySummary>(`/strava/activity/${id}`),
  getRecentSummary: () => apiClient.get<RecentSummary>('/strava/recent-summary'),
};
