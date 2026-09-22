import api from './client';

export const inboxApi = {
  getThreads: (params = {}) => api.get('/inbox/threads', params),
  getCounts: (userEmail) => api.get('/inbox/counts', { user_email: userEmail }),
  getThreadDetail: (threadId) => api.get(`/inbox/threads/${threadId}`),
  syncInbox: (userEmail) => api.post('/inbox/sync', { user_email: userEmail }),
  starThread: (threadId, isStarred = true) => api.post(`/inbox/threads/${threadId}/star`, null, { params: { is_starred: isStarred } }),
  markRead: (threadId, isRead = true) => api.post(`/inbox/threads/${threadId}/read`, null, { params: { is_read: isRead } }),
  archiveThread: (threadId) => api.post(`/inbox/threads/${threadId}/archive`),
  trashThread: (threadId) => api.post(`/inbox/threads/${threadId}/trash`),
  spamThread: (threadId) => api.post(`/inbox/threads/${threadId}/spam`),
  snoozeThread: (threadId, until) => api.post(`/inbox/threads/${threadId}/snooze`, { until }),
  analyzeThread: (threadId) => api.post(`/inbox/threads/${threadId}/analyze`),
  analyzeWritingStyle: (userEmail) => api.post('/inbox/analyze-writing-style', null, { params: { user_email: userEmail } }),
  sendReply: (threadId, payload) => api.post(`/inbox/threads/${threadId}/send-reply`, payload),
  assignThread: (threadId, assignedTo) => api.post(`/inbox/threads/${threadId}/assign`, { assigned_to: assignedTo }),
  unassignThread: (threadId) => api.post(`/inbox/threads/${threadId}/unassign`),
};

export default inboxApi;
