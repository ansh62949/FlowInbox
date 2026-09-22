import api from './client';

export const channelsApi = {
  getChannels: () => api.get('/channels'),
  createChannel: (name, icon = 'hash', rules = []) => api.post('/channels', { name, icon, rules }),
  getChannelFilters: (channelId) => api.get(`/channels/${channelId}/filters`),
};

export default channelsApi;
