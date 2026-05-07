import { createRouter, createWebHistory } from 'vue-router';
import { useAuthStore } from '@/stores/auth';

const routes = [
    {
        path: '/login',
        name: 'Login',
        component: () => import('@/views/auth/Login.vue'),
        meta: { guest: true },
    },
    {
        path: '/',
        component: () => import('@/layouts/MainLayout.vue'),
        meta: { requiresAuth: true },
        children: [
            { path: '', redirect: '/dashboard' },
            { path: 'dashboard', name: 'Dashboard', component: () => import('@/views/dashboard/Index.vue'), meta: { title: '概览仪表盘' } },
            { path: 'documents', name: 'Documents', component: () => import('@/views/document/Index.vue'), meta: { title: '文件管理' } },
            { path: 'documents/:id', name: 'DocumentDetail', component: () => import('@/views/document/Detail.vue'), meta: { title: '文件详情' } },
            { path: 'upload', name: 'Upload', component: () => import('@/views/upload/Index.vue'), meta: { title: '上传录入' } },
            { path: 'pipeline', name: 'Pipeline', component: () => import('@/views/pipeline/Index.vue'), meta: { title: '数据管道' } },
            { path: 'ai', name: 'AI', component: () => import('@/views/ai/Index.vue'), meta: { title: '业务大模型' } },
            { path: 'review', name: 'Review', component: () => import('@/views/review/Index.vue'), meta: { title: '人工核对' } },
            { path: 'orders', name: 'Orders', component: () => import('@/views/order/Index.vue'), meta: { title: '订单管理' } },
            { path: 'customers', name: 'Customers', component: () => import('@/views/customer/Index.vue'), meta: { title: '客户管理' } },
            { path: 'reports', name: 'Reports', component: () => import('@/views/reports/Index.vue'), meta: { title: '数据报表' } },
            { path: 'settings', name: 'Settings', component: () => import('@/views/settings/Index.vue'), meta: { title: '系统设置' } },
        ],
    },
];

const router = createRouter({
    history: createWebHistory(),
    routes,
});

// 路由守卫
router.beforeEach(async (to, from, next) => {
    const auth = useAuthStore();

    if (to.meta.requiresAuth && !auth.isLoggedIn) {
        return next('/login');
    }

    if (to.meta.guest && auth.isLoggedIn) {
        return next('/dashboard');
    }

    // 已登录但未获取用户信息
    if (auth.isLoggedIn && !auth.user) {
        await auth.fetchUser();
    }

    next();
});

export default router;
