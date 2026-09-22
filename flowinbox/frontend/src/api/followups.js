import api from './client';

export const followupsApi = {
  getCandidates: () => api.get('/followups/candidates'),
  getConfig: () => api.get('/followups/config'),
  updateConfig: (data) => api.post('/followups/config', data),
  simulate: () => api.post('/followups/simulate'),
};

export default followupsApi;
