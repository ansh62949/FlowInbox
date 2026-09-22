import api from './client';

export const draftsApi = {
  getDrafts: () => api.get('/drafts'),
  updateDraft: (draftId, bodyText) => api.put(`/drafts/${draftId}`, { body: bodyText }),
};

export default draftsApi;
