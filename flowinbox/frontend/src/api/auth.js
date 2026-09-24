import api, { API_BASE } from './client';

export const authApi = {
  getMe: () => api.get('/auth/me'),
  getGoogleStatus: () => api.get('/auth/google/status'),
  getWritingProfile: () => api.get('/auth/writing-profile'),
  updateWritingProfile: (data) => api.post('/auth/writing-profile', data),
  completeOnboarding: () => api.post('/auth/complete-onboarding'),
  enterDemo: () => api.post('/auth/demo'),
  getLoginUrl: () => `${API_BASE}/auth/google/login`,
};

export default authApi;

