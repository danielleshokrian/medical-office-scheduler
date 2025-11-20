const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://127.0.0.1:5001';

 

// Remove trailing slash if present

const normalizedApiUrl = API_BASE_URL.replace(/\/$/, '');

 

export const API_URL = normalizedApiUrl;

 

// Helper function to build full API URLs

export const buildApiUrl = (path) => {

  // Remove leading slash if present to avoid double slashes

  const normalizedPath = path.startsWith('/') ? path.slice(1) : path;

  return `${API_URL}/${normalizedPath}`;

};

 

// Common API endpoints

export const API_ENDPOINTS = {

  // Auth

  AUTH_LOGIN: buildApiUrl('auth/login'),

  AUTH_REGISTER: buildApiUrl('auth/register'),

  AUTH_REFRESH: buildApiUrl('auth/refresh'),

  AUTH_ME: buildApiUrl('auth/me'),

 

  // Staff

  STAFF: buildApiUrl('staff'),

  STAFF_BY_ID: (id) => buildApiUrl(`staff/${id}`),

  STAFF_SCHEDULE: (id) => buildApiUrl(`staff/${id}/schedule`),

 

  // Shifts

  SHIFTS: buildApiUrl('shifts'),

  SHIFTS_BY_ID: (id) => buildApiUrl(`shifts/${id}`),

 

  // Areas

  AREAS: buildApiUrl('areas'),

  AREAS_BY_ID: (id) => buildApiUrl(`areas/${id}`),

  COVERAGE: (areaId, date) => buildApiUrl(`coverage/${areaId}/${date}`),

 

  // Time Off

  TIME_OFF: buildApiUrl('time-off'),

  TIME_OFF_BY_ID: (id) => buildApiUrl(`time-off/${id}`),

 

  // AI Scheduling

  AI_GENERATE: buildApiUrl('ai/generate-schedule'),

  AI_APPLY: buildApiUrl('ai/apply-schedule'),

 

  // Health

  HEALTH: buildApiUrl('health'),

  READY: buildApiUrl('ready'),

};

 

// Export config object for convenience

export default {

  API_URL,

  buildApiUrl,

  API_ENDPOINTS,

};