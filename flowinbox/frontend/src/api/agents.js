import api from './client';

export const agentsApi = {
  submitTask: (userId, request) => api.post('/agent/tasks', { user_id: userId, request }),
  getTaskStatus: (taskId) => api.get(`/agent/tasks/${taskId}`),
  listAgents: (workspaceId) => api.get('/agents', workspaceId ? { workspace_id: workspaceId } : {}),
  getAgentDetail: (agentId) => api.get(`/agents/${agentId}`),
  getAgentActivity: (agentId) => api.get(`/agents/${agentId}/activity`),
};

export default agentsApi;
