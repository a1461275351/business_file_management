import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { authApi } from '@/api/auth';

export const useAuthStore = defineStore('auth', () => {
    const token = ref(localStorage.getItem('token') || '');
    const user = ref(null);

    const isLoggedIn = computed(() => !!token.value);
    const userName = computed(() => user.value?.real_name || '');
    const userRoles = computed(() => user.value?.roles?.map(r => r.name) || []);
    const userPermissions = computed(() => user.value?.permissions?.map(p => p.name) || []);

    function hasPermission(permission) {
        if (userRoles.value.includes('super_admin')) return true;
        return userPermissions.value.includes(permission);
    }

    function hasRole(role) {
        return userRoles.value.includes(role);
    }

    async function login(credentials) {
        const res = await authApi.login(credentials);
        token.value = res.data.token;
        user.value = res.data.user;
        localStorage.setItem('token', res.data.token);
        return res;
    }

    async function fetchUser() {
        try {
            const res = await authApi.me();
            user.value = res.data;
        } catch {
            logout();
        }
    }

    function logout() {
        token.value = '';
        user.value = null;
        localStorage.removeItem('token');
    }

    return {
        token, user, isLoggedIn, userName, userRoles, userPermissions,
        hasPermission, hasRole, login, fetchUser, logout,
    };
});
