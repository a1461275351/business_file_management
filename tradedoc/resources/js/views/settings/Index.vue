<template>
  <div class="settings-page">
    <el-tabs v-model="activeTab">
      <!-- 用户管理 -->
      <el-tab-pane label="用户管理" name="users">
        <div class="tab-header">
          <span class="tab-title">用户列表</span>
          <el-button type="primary" size="small"><el-icon><Plus /></el-icon> 添加用户</el-button>
        </div>
        <el-table :data="users" size="small" stripe v-loading="usersLoading">
          <el-table-column label="用户名" prop="username" width="120" />
          <el-table-column label="姓名" prop="real_name" width="100" />
          <el-table-column label="角色" width="120">
            <template #default="{ row }">
              <el-tag v-for="r in row.roles" :key="r.name" size="small" class="mr-4">{{ r.display_name || r.name }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="部门" width="100">
            <template #default="{ row }">{{ row.department?.name || '—' }}</template>
          </el-table-column>
          <el-table-column label="邮箱" prop="email" min-width="180" />
          <el-table-column label="状态" width="80">
            <template #default="{ row }">
              <el-tag :type="row.status === 1 ? 'success' : 'danger'" size="small">{{ row.status === 1 ? '正常' : '禁用' }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="最后登录" width="160">
            <template #default="{ row }">{{ row.last_login_at ? new Date(row.last_login_at).toLocaleString('zh-CN') : '—' }}</template>
          </el-table-column>
          <el-table-column label="操作" width="80">
            <template #default>
              <el-button link type="primary" size="small">编辑</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- 字段模板 -->
      <el-tab-pane label="字段模板" name="templates">
        <div class="tab-header">
          <span class="tab-title">字段提取模板管理</span>
        </div>
        <el-table :data="docTypes" size="small" stripe v-loading="typesLoading">
          <el-table-column label="文件类型" width="120">
            <template #default="{ row }">
              <span>{{ row.icon }} {{ row.name }}</span>
            </template>
          </el-table-column>
          <el-table-column label="英文名" prop="name_en" width="160" />
          <el-table-column label="字段数" width="80">
            <template #default="{ row }">{{ row.field_count || 0 }}</template>
          </el-table-column>
          <el-table-column label="编码" prop="code" min-width="180" />
          <el-table-column label="操作" width="120">
            <template #default="{ row }">
              <el-button link type="primary" size="small" @click="viewTemplate(row)">查看字段</el-button>
            </template>
          </el-table-column>
        </el-table>

        <!-- 字段详情弹窗 -->
        <el-dialog v-model="templateDialogVisible" :title="`${currentType?.name} — 字段模板`" width="600px">
          <el-table :data="currentFields" size="small" stripe>
            <el-table-column label="字段名" prop="field_name" width="100" />
            <el-table-column label="英文" prop="field_name_en" width="120" />
            <el-table-column label="标识" prop="field_key" width="150" />
            <el-table-column label="类型" prop="field_type" width="80" />
            <el-table-column label="必填" width="60" align="center">
              <template #default="{ row }"><span v-if="row.is_required" style="color:#f56c6c">*</span></template>
            </el-table-column>
            <el-table-column label="自动提取" width="80" align="center">
              <template #default="{ row }">
                <el-tag :type="row.is_auto_extract ? 'success' : 'info'" size="small">{{ row.is_auto_extract ? '是' : '否' }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-dialog>
      </el-tab-pane>

      <!-- OCR 引擎 -->
      <el-tab-pane label="识别引擎" name="ocr">
        <div class="tab-header">
          <span class="tab-title">识别引擎状态</span>
          <el-button size="small" @click="loadOcrStatus"><el-icon><Refresh /></el-icon> 刷新</el-button>
        </div>
        <el-descriptions :column="2" border size="small" v-loading="ocrLoading">
          <el-descriptions-item label="引擎模式">
            <el-tag :type="ocrStatus.engine_mode === 'aliyun_api' ? 'success' : ocrStatus.engine_mode === 'local_model' ? '' : 'warning'" size="small">
              {{ engineModeMap[ocrStatus.engine_mode] || ocrStatus.engine_mode }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="API Key">
            <el-tag :type="ocrStatus.api_key_set ? 'success' : 'danger'" size="small">
              {{ ocrStatus.api_key_set ? '已配置' : '未配置' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="本地模型">
            <el-tag :type="ocrStatus.model_loaded ? 'success' : 'info'" size="small">
              {{ ocrStatus.model_loaded ? '已加载' : '未安装' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="模型路径">{{ ocrStatus.model_path || '—' }}</el-descriptions-item>
        </el-descriptions>
        <div class="ocr-tip">
          <p>当前支持三种识别模式：</p>
          <ul>
            <li><strong>阿里云 API</strong> — qwen-vl-ocr-latest，无需 GPU，推荐</li>
            <li><strong>本地模型</strong> — Logics-Parsing-v2，需 NVIDIA GPU ≥ 8GB</li>
            <li><strong>模拟模式</strong> — 返回测试数据，开发调试用</li>
          </ul>
        </div>
      </el-tab-pane>

      <!-- 系统信息 -->
      <el-tab-pane label="系统信息" name="system">
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="系统名称">贸易云档 TradeDoc</el-descriptions-item>
          <el-descriptions-item label="版本">v1.0.0</el-descriptions-item>
          <el-descriptions-item label="PHP 版本">8.5.5</el-descriptions-item>
          <el-descriptions-item label="运行模式">RoadRunner (Octane)</el-descriptions-item>
          <el-descriptions-item label="数据库">MySQL 8.0</el-descriptions-item>
          <el-descriptions-item label="Python 服务">FastAPI (:8100)</el-descriptions-item>
        </el-descriptions>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import http from '@/api/http';
import { documentApi } from '@/api/document';

const activeTab = ref('users');

// 用户管理
const users = ref([]);
const usersLoading = ref(false);

// 字段模板
const docTypes = ref([]);
const typesLoading = ref(false);
const templateDialogVisible = ref(false);
const currentType = ref(null);
const currentFields = ref([]);

// OCR
const ocrStatus = ref({});
const ocrLoading = ref(false);

const engineModeMap = { aliyun_api: '阿里云 API', local_model: '本地模型', mock: '模拟模式' };

async function loadUsers() {
    usersLoading.value = true;
    try {
        const res = await http.get('/admin/users');
        users.value = res.data;
    } catch {
        // 如果接口未实现，显示空
        users.value = [];
    } finally {
        usersLoading.value = false;
    }
}

async function loadDocTypes() {
    typesLoading.value = true;
    try {
        const res = await documentApi.types();
        // 获取每个类型的字段数
        const types = res.data;
        for (const t of types) {
            try {
                const fieldsRes = await http.get(`/admin/field-templates/${t.id}`);
                t.field_count = fieldsRes.data?.length || 0;
            } catch {
                t.field_count = 0;
            }
        }
        docTypes.value = types;
    } finally {
        typesLoading.value = false;
    }
}

async function viewTemplate(type) {
    currentType.value = type;
    try {
        const res = await http.get(`/admin/field-templates/${type.id}`);
        currentFields.value = res.data;
    } catch {
        currentFields.value = [];
    }
    templateDialogVisible.value = true;
}

async function loadOcrStatus() {
    ocrLoading.value = true;
    try {
        ocrStatus.value = await http.get('/ocr/engine-status');
    } catch {
        ocrStatus.value = { engine_mode: 'offline', api_key_set: false, model_loaded: false };
    } finally {
        ocrLoading.value = false;
    }
}

onMounted(() => {
    loadUsers();
    loadDocTypes();
    loadOcrStatus();
});
</script>

<style scoped>
.settings-page :deep(.el-tabs__content) { padding-top: 8px; }
.tab-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.tab-title { font-size: 14px; font-weight: 600; }
.mr-4 { margin-right: 4px; }
.ocr-tip { margin-top: 16px; font-size: 13px; color: #606266; }
.ocr-tip ul { margin-top: 8px; padding-left: 20px; }
.ocr-tip li { margin-bottom: 4px; }
</style>
