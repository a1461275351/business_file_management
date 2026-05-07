import http from './http';

export const reviewApi = {
    list: (params) => http.get('/reviews', { params }),
    statistics: () => http.get('/reviews/statistics'),
    detail: (id) => http.get(`/reviews/${id}`),
    confirm: (id, fields) => http.post(`/reviews/${id}/confirm`, { fields }),
    skip: (id) => http.post(`/reviews/${id}/skip`),
};
