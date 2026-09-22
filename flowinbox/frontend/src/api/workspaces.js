import api from './client';

export const workspacesApi = {
  getWorkspaces: () => api.get('/workspaces'),
  createWorkspace: (name, slug) => api.post('/workspaces', { name, slug }),
  getMembers: (workspaceId) => api.get(`/workspaces/${workspaceId}/members`),
  inviteMember: (workspaceId, email, role = 'MEMBER') => api.post(`/workspaces/${workspaceId}/members`, { email, role }),
};

export default workspacesApi;
