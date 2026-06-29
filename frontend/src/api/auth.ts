import { apiClient } from './client';
import type { AuthCallbackPayload, AuthCallbackResponse, StravaUrlResponse } from '../types/api';

export const authApi = {
  getStravaUrl: () => apiClient.getPublic<StravaUrlResponse>('/auth/strava/url'),

  exchangeCode: (payload: AuthCallbackPayload) =>
    apiClient.postPublic<AuthCallbackResponse>('/auth/strava/callback', payload),
};
