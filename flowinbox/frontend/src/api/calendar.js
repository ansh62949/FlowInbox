import api from './client';

export const calendarApi = {
  getEvents: () => api.get('/calendar/events'),
};

export default calendarApi;
