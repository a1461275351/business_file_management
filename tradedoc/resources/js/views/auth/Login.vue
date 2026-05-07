<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-header">
        <span class="login-logo">📄</span>
        <h1>贸易云档</h1>
        <p>TradeDoc Intelligence Platform</p>
      </div>

      <el-form ref="formRef" :model="form" :rules="rules" @submit.prevent="handleLogin" class="login-form">
        <el-form-item prop="username">
          <el-input
            v-model="form.username"
            placeholder="用户名"
            size="large"
            :prefix-icon="User"
          />
        </el-form-item>
        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="密码"
            size="large"
            :prefix-icon="Lock"
            show-password
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" size="large" :loading="loading" @click="handleLogin" class="login-btn">
            登 录
          </el-button>
        </el-form-item>
      </el-form>

      <div class="login-footer">
        外贸文件智能管理系统 v1.0
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue';
import { useRouter } from 'vue-router';
import { User, Lock } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';
import { useAuthStore } from '@/stores/auth';

const router = useRouter();
const auth = useAuthStore();
const formRef = ref(null);
const loading = ref(false);

const form = reactive({
    username: '',
    password: '',
});

const rules = {
    username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
    password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
};

async function handleLogin() {
    const valid = await formRef.value.validate().catch(() => false);
    if (!valid) return;

    loading.value = true;
    try {
        await auth.login(form);
        ElMessage.success('登录成功');
        router.push('/dashboard');
    } catch {
        // 错误已在 http 拦截器中处理
    } finally {
        loading.value = false;
    }
}
</script>

<style scoped>
.login-page {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #0c447c 0%, #185fa5 50%, #378add 100%);
}
.login-card {
  width: 400px;
  background: #fff;
  border-radius: 12px;
  padding: 40px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.15);
}
.login-header {
  text-align: center;
  margin-bottom: 32px;
}
.login-logo {
  font-size: 40px;
  display: block;
  margin-bottom: 12px;
}
.login-header h1 {
  font-size: 22px;
  font-weight: 600;
  color: #1a1a18;
  margin: 0 0 4px;
}
.login-header p {
  font-size: 13px;
  color: #888;
  margin: 0;
}
.login-btn {
  width: 100%;
}
.login-footer {
  text-align: center;
  font-size: 12px;
  color: #ccc;
  margin-top: 24px;
}
</style>
