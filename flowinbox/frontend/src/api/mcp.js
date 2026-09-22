import api from './client';

export const mcpApi = {
  callTool: (name, args = {}) => api.post('/mcp/tools/call', { name, arguments: args }),
};

export default mcpApi;
