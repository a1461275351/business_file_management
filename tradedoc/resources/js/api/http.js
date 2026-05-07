import axios from 'axios';
import { ElMessage } from 'element-plus';
import { useAuthStore } from '@/stores/auth';
import router from '@/router';

const http = axios.create({
    baseURL: '/api/v1',
    timeout: 30000,
    headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    },
});

// 请求拦截：自动带上 Token
http.interceptors.request.use((config) => {
    const auth = useAuthStore();
    if (auth.token) {
        config.headers.Authorization = `Bearer ${auth.token}`;
    }
    return config;
});

// 响应拦截：统一错误处理
http.interceptors.response.use(
    (response) => response.data,
    (error) => {
        const { status, data } = error.response || {};

        if (status === 401) {
            const auth = useAuthStore();
            auth.logout();
            router.push('/login');
            ElMessage.error('登录已过期，请重新登录');
        } else if (status === 403) {
            ElMessage.error('没有操作权限');
        } else if (status === 422) {
            // 表单验证错误
            const firstError = Object.values(data.errors || {})[0];
            ElMessage.error(firstError?.[0] || '参数验证失败');
        } else if (status >= 500) {
            ElMessage.error('服务器错误，请稍后重试');
        } else {
            ElMessage.error(data?.message || '请求失败');
        }

        return Promise.reject(error);
    }
);

export default http;
