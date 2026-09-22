import api from './client';

export const approvalsApi = {
  getPendingApprovals: () => api.get('/approvals'),
  approve: (approvalId) => api.post(`/approvals/${approvalId}/approve`),
  reject: (approvalId) => api.post(`/approvals/${approvalId}/reject`),
};

export default approvalsApi;
