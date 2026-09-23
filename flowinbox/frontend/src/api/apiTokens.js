import api from './client';

export const apiTokensApi = {
  list: () => api.get('/api-tokens'),
  create: (name) => api.post('/api-tokens', { name }),
  revoke: (tokenId) => api.delete(`/api-tokens/${tokenId}`),
};

export default apiTokensApi;
