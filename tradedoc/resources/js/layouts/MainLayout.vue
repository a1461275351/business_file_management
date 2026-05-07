<template>
  <el-container class="layout-container">
    <!-- 侧边栏 -->
    <el-aside :width="isCollapse ? '64px' : '200px'" class="layout-aside">
      <div class="logo-area" @click="$router.push('/dashboard')">
        <span class="logo-icon">📄</span>
        <span v-show="!isCollapse" class="logo-text">贸易云档</span>
      </div>

      <el-menu
        :default-active="activeMenu"
        :collapse="isCollapse"
        router
        class="sidebar-menu"
        background-color="#1d1e2c"
        text-color="#a0a1b1"
        active-text-color="#409eff"
      >
        <el-menu-item index="/dashboard">
          <el-icon><DataBoard /></el-icon>
          <template #title>概览仪表盘</template>
        </el-menu-item>
        <el-menu-item index="/documents">
          <el-icon><Document /></el-icon>
          <template #title>文件管理</template>
        </el-menu-item>
        <el-menu-item index="/upload">
          <el-icon><Upload /></el-icon>
          <template #title>上传录入</template>
        </el-menu-item>
        <el-menu-item index="/review" v-if="auth.hasPermission('review.list')">
          <el-icon><EditPen /></el-icon>
          <template #title>人工核对</template>
        </el-menu-item>
        <el-menu-item index="/orders">
          <el-icon><List /></el-icon>
          <template #title>订单管理</template>
        </el-menu-item>
        <el-menu-item index="/customers">
          <el-icon><OfficeBuilding /></el-icon>
          <template #title>客户管理</template>
        </el-menu-item>
        <el-menu-item index="/pipeline">
          <el-icon><Connection /></el-icon>
          <template #title>数据管道</template>
        </el-menu-item>
        <el-menu-item index="/ai">
          <el-icon><ChatDotRound /></el-icon>
          <template #title>业务大模型</template>
        </el-menu-item>
        <el-menu-item index="/reports" v-if="auth.hasPermission('report.view')">
          <el-icon><DataAnalysis /></el-icon>
          <template #title>数据报表</template>
        </el-menu-item>
        <el-menu-item index="/settings" v-if="auth.hasPermission('system.config')">
          <el-icon><Setting /></el-icon>
          <template #title>系统设置</template>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <!-- 右侧内容区 -->
    <el-container>
      <!-- 顶栏 -->
      <el-header class="layout-header">
        <div class="header-left">
          <el-icon class="collapse-btn" @click="isCollapse = !isCollapse">
            <Fold v-if="!isCollapse" /><Expand v-else />
          </el-icon>
          <span class="page-title">{{ $route.meta.title || '' }}</span>
        </div>
        <div class="header-right">
          <el-badge :value="unreadCount" :hidden="unreadCount === 0" :max="99" class="notify-badge">
            <el-icon class="header-icon"><Bell /></el-icon>
          </el-badge>
          <el-dropdown trigger="click" @command="handleUserCommand">
            <span class="user-info">
              <el-avatar :size="28" class="user-avatar">{{ auth.userName?.charAt(0) || 'U' }}</el-avatar>
              <span class="user-name">{{ auth.userName }}</span>
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">个人信息</el-dropdown-item>
                <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <!-- 主内容 -->
      <el-main class="layout-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import { notificationApi } from '@/api/notification';

const route = useRoute();
const router = useRouter();
const auth = useAuthStore();

const isCollapse = ref(false);
const unreadCount = ref(0);
const activeMenu = computed(() => '/' + (route.path.split('/')[1] || 'dashboard'));

async function loadUnreadCount() {
    try {
        const res = await notificationApi.unreadCount();
        unreadCount.value = res.data.count;
    } catch {}
}

onMounted(() => {
    loadUnreadCount();
    // 每30秒刷新未读数
    setInterval(loadUnreadCount, 30000);
});

function handleUserCommand(command) {
    if (command === 'logout') {
        auth.logout();
        router.push('/login');
    }
}
</script>

<style scoped>
.layout-container {
  height: 100vh;
}
.layout-aside {
  background: #1d1e2c;
  transition: width 0.3s;
  overflow: hidden;
}
.logo-area {
  height: 56px;
  display: flex;
  align-items: center;
  padding: 0 16px;
  cursor: pointer;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}
.logo-icon { font-size: 22px; }
.logo-text {
  font-size: 15px;
  font-weight: 600;
  color: #fff;
  margin-left: 10px;
  white-space: nowrap;
}
.sidebar-menu {
  border-right: none;
}
.layout-header {
  background: #fff;
  border-bottom: 1px solid #e8e8e8;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  height: 56px;
}
.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}
.collapse-btn {
  font-size: 20px;
  cursor: pointer;
  color: #666;
}
.page-title {
  font-size: 15px;
  font-weight: 500;
  color: #333;
}
.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}
.header-icon {
  font-size: 18px;
  cursor: pointer;
  color: #666;
}
.notify-badge { cursor: pointer; }
.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  color: #333;
}
.user-name { font-size: 13px; }
.layout-main {
  background: #f5f5f5;
  padding: 20px;
}
</style>
