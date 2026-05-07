import http from './http';

export const authApi = {
    login: (data) => http.post('/auth/login', data),
    logout: () => http.post('/auth/logout'),
    me: () => http.get('/auth/me'),
};
