import { API_ENDPOINTS } from './config';

export const fetchWithAuth = async (url, options = {}) => {
  const token = localStorage.getItem('access_token');
  
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers
  };
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  const response = await fetch(url, {
    ...options,
    headers
  });
  
  if (response.status === 401) {
    const refreshToken = localStorage.getItem('refresh_token');
    if (refreshToken) {
      const refreshResponse = await fetch(API_ENDPOINTS.AUTH_REFRESH, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${refreshToken}`
        }
      });
      
      if (refreshResponse.ok) {
        const data = await refreshResponse.json();
        localStorage.setItem('access_token', data.access_token);
        
        headers['Authorization'] = `Bearer ${data.access_token}`;
        return fetch(url, { ...options, headers });
      }
    }
    
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    window.location.href = '/login';
  }
  
  return response;
};