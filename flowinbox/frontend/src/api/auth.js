import api from './client';

export const authApi = {
  getMe: () => api.get('/auth/me'),
  getGoogleStatus: () => api.get('/auth/google/status'),
  getWritingProfile: () => api.get('/auth/writing-profile'),
  updateWritingProfile: (data) => api.post('/auth/writing-profile', data),
  completeOnboarding: () => api.post('/auth/complete-onboarding'),
  getLoginUrl: () => '/api/v1/auth/google/login',
};

export default authApi;
