import api from './client';

export const integrationsApi = {
  list: () => api.get('/integrations'),
};

export default integrationsApi;
