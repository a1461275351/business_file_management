import http from './http';

export const documentApi = {
    // 文件类型列表
    types: () => http.get('/document-types'),

    // 上传文件
    upload: (formData, onProgress) => http.post('/documents/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: onProgress,
    }),

    // 批量上传
    batchUpload: (formData, onProgress) => http.post('/documents/batch-upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: onProgress,
    }),

    // 文件列表
    list: (params) => http.get('/documents', { params }),

    // 文件详情
    detail: (id) => http.get(`/documents/${id}`),

    // 删除文件
    delete: (id) => http.delete(`/documents/${id}`),

    // 变更状态
    changeStatus: (id, status) => http.put(`/documents/${id}/status`, { status }),

    // 下载原件（返回 blob）
    download: (id) => http.get(`/documents/${id}/download`, { responseType: 'blob' }),

    // 预览地址
    previewUrl: (id) => `/api/v1/documents/${id}/preview`,

    // 更新字段
    updateField: (fieldId, value) => http.post('/documents/update-field', { field_id: fieldId, value }),

    // 仪表盘统计
    statistics: () => http.get('/documents/statistics'),
};
