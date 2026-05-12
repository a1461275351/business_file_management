<template>
  <div class="settings-page">
    <el-tabs v-model="activeTab">
      <!-- 用户管理 -->
      <el-tab-pane label="用户管理" name="users">
        <div class="tab-header">
          <span class="tab-title">用户列表</span>
          <el-button type="primary" size="small" @click="openCreateDialog">
            <el-icon><Plus /></el-icon> 添加用户
          </el-button>
        </div>
        <el-table :data="users" size="small" stripe v-loading="usersLoading">
          <el-table-column label="用户名" prop="username" width="120" />
          <el-table-column label="姓名" prop="real_name" width="100" />
          <el-table-column label="角色" width="140">
            <template #default="{ row }">
              <el-tag v-for="r in row.roles" :key="r.name" size="small" class="mr-4">{{ r.display_name || r.name }}</el-tag>
              <span v-if="!row.roles?.length" class="text-light">—</span>
            </template>
          </el-table-column>
          <el-table-column label="部门" width="100">
            <template #default="{ row }">{{ row.department?.name || '—' }}</template>
          </el-table-column>
          <el-table-column label="邮箱" prop="email" min-width="180">
            <template #default="{ row }">{{ row.email || '—' }}</template>
          </el-table-column>
          <el-table-column label="手机" prop="phone" width="120">
            <template #default="{ row }">{{ row.phone || '—' }}</template>
          </el-table-column>
          <el-table-column label="状态" width="80">
            <template #default="{ row }">
              <el-tag :type="row.status === 1 ? 'success' : 'danger'" size="small">{{ row.status === 1 ? '正常' : '禁用' }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="最后登录" width="160">
            <template #default="{ row }">{{ row.last_login_at ? new Date(row.last_login_at).toLocaleString('zh-CN') : '—' }}</template>
          </el-table-column>
          <el-table-column label="操作" width="150" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" size="small" @click="openEditDialog(row)">编辑</el-button>
              <el-button link type="danger" size="small" @click="confirmDelete(row)" :disabled="row.username === 'admin'">删除</el-button>
            </template>
          </el-table-column>
        </el-table>

        <!-- 新建/编辑用户对话框 -->
        <el-dialog v-model="userDialogVisible" :title="userFormMode === 'create' ? '新建用户' : '编辑用户：' + userForm.username" width="540px" :close-on-click-modal="false">
          <el-form :model="userForm" :rules="userFormRules" ref="userFormRef" label-width="86px" size="small">
            <el-form-item label="用户名" prop="username">
              <el-input v-model="userForm.username" :disabled="userFormMode === 'edit'" placeholder="登录用，如 zhangsan" />
              <div class="form-tip" v-if="userFormMode === 'edit'">用户名创建后不可修改</div>
            </el-form-item>

            <el-form-item label="真实姓名" prop="real_name">
              <el-input v-model="userForm.real_name" placeholder="如 张三" />
            </el-form-item>

            <el-form-item :label="userFormMode === 'create' ? '初始密码' : '新密码'" prop="password">
              <el-input v-model="userForm.password" type="password" show-password :placeholder="userFormMode === 'create' ? '至少 6 位' : '留空表示不修改密码'" />
              <div class="form-tip" v-if="userFormMode === 'edit'">填写则修改密码，留空保持原密码</div>
            </el-form-item>

            <el-form-item label="角色" prop="role">
              <el-select v-model="userForm.role" placeholder="选择角色" style="width:100%">
                <el-option v-for="r in roleOptions" :key="r.name" :label="r.display_name || r.name" :value="r.name" />
              </el-select>
            </el-form-item>

            <el-form-item label="邮箱">
              <el-input v-model="userForm.email" placeholder="选填，用于密码找回（待实现）" />
            </el-form-item>

            <el-form-item label="手机">
              <el-input v-model="userForm.phone" placeholder="选填" />
            </el-form-item>

            <el-form-item label="部门 ID">
              <el-input-number v-model="userForm.department_id" :min="0" placeholder="选填" controls-position="right" style="width:100%" />
              <div class="form-tip">暂无部门管理页面，可留空</div>
            </el-form-item>

            <el-form-item label="状态" v-if="userFormMode === 'edit'">
              <el-radio-group v-model="userForm.status">
                <el-radio :value="1">启用</el-radio>
                <el-radio :value="0">禁用</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-form>

          <template #footer>
            <el-button @click="userDialogVisible = false">取消</el-button>
            <el-button type="primary" :loading="userFormSubmitting" @click="submitUser">
              {{ userFormMode === 'create' ? '创建' : '保存' }}
            </el-button>
          </template>
        </el-dialog>
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
          <el-descriptions-item label="运行模式">PHP-CGI (phpStudy)</el-descriptions-item>
          <el-descriptions-item label="数据库">MySQL 8.0</el-descriptions-item>
          <el-descriptions-item label="Python 服务">FastAPI (:8100)</el-descriptions-item>
        </el-descriptions>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import http from '@/api/http';
import { documentApi } from '@/api/document';

const activeTab = ref('users');

// 用户管理
const users = ref([]);
const usersLoading = ref(false);
const userDialogVisible = ref(false);
const userFormMode = ref('create');     // create | edit
const userFormSubmitting = ref(false);
const userFormRef = ref(null);
const roleOptions = ref([]);
const editingUserId = ref(null);

const userForm = reactive({
    username: '',
    real_name: '',
    password: '',
    email: '',
    phone: '',
    department_id: null,
    role: '',
    status: 1,
});

const userFormRules = {
    username: [
        { required: true, message: '请输入用户名', trigger: 'blur' },
        { min: 2, max: 50, message: '用户名 2-50 个字符', trigger: 'blur' },
        { pattern: /^[a-zA-Z0-9_]+$/, message: '只能用字母、数字、下划线', trigger: 'blur' },
    ],
    real_name: [
        { required: true, message: '请输入真实姓名', trigger: 'blur' },
    ],
    password: [
        {
            validator: (rule, value, callback) => {
                if (userFormMode.value === 'create' && !value) {
                    callback(new Error('请设置初始密码'));
                } else if (value && value.length < 6) {
                    callback(new Error('密码至少 6 位'));
                } else {
                    callback();
                }
            },
            trigger: 'blur',
        },
    ],
    role: [{ required: true, message: '请选择角色', trigger: 'change' }],
};

function resetUserForm() {
    userForm.username = '';
    userForm.real_name = '';
    userForm.password = '';
    userForm.email = '';
    userForm.phone = '';
    userForm.department_id = null;
    userForm.role = '';
    userForm.status = 1;
    editingUserId.value = null;
    userFormRef.value?.clearValidate();
}

async function openCreateDialog() {
    resetUserForm();
    userFormMode.value = 'create';
    if (roleOptions.value.length === 0) {
        await loadRoles();
    }
    userDialogVisible.value = true;
}

async function openEditDialog(user) {
    resetUserForm();
    userFormMode.value = 'edit';
    editingUserId.value = user.id;
    userForm.username = user.username;
    userForm.real_name = user.real_name || '';
    userForm.email = user.email || '';
    userForm.phone = user.phone || '';
    userForm.department_id = user.department_id || null;
    userForm.role = user.roles?.[0]?.name || '';
    userForm.status = user.status ?? 1;
    if (roleOptions.value.length === 0) {
        await loadRoles();
    }
    userDialogVisible.value = true;
}

async function submitUser() {
    if (userFormSubmitting.value) return;     // 防止重复提交（双击/连点）
    if (!userFormRef.value) return;

    userFormSubmitting.value = true;          // 立即锁住，validate 之前就锁
    try {
        const valid = await userFormRef.value.validate().catch(() => false);
        if (!valid) {
            userFormSubmitting.value = false;
            return;
        }

        if (userFormMode.value === 'create') {
            const payload = {
                username: userForm.username,
                real_name: userForm.real_name,
                password: userForm.password,
                email: userForm.email || null,
                phone: userForm.phone || null,
                department_id: userForm.department_id || null,
                role: userForm.role,
            };
            await http.post('/admin/users', payload);
            ElMessage.success('用户创建成功');
        } else {
            const payload = {
                real_name: userForm.real_name,
                email: userForm.email || null,
                phone: userForm.phone || null,
                department_id: userForm.department_id || null,
                role: userForm.role,
                status: userForm.status,
            };
            if (userForm.password) {
                payload.password = userForm.password;
            }
            await http.put(`/admin/users/${editingUserId.value}`, payload);
            ElMessage.success('用户信息已更新');
        }

        // 关键：成功后立即关对话框（无论 loadUsers 是否成功，已经成功的不能再被当成失败）
        userDialogVisible.value = false;
        loadUsers();      // 不 await，后台刷新，失败也不影响成功体验
    } catch (err) {
        // http 拦截器已经弹错误提示
    } finally {
        userFormSubmitting.value = false;
    }
}

async function confirmDelete(user) {
    try {
        await ElMessageBox.confirm(
            `确定删除用户 ${user.username} (${user.real_name}) 吗？删除后该用户无法登录，但历史操作记录保留。`,
            '确认删除',
            { type: 'warning', confirmButtonText: '确认删除', cancelButtonText: '取消' }
        );
    } catch {
        return;
    }
    try {
        await http.delete(`/admin/users/${user.id}`);
        ElMessage.success('用户已删除');
        await loadUsers();
    } catch {
        // 拦截器已处理
    }
}

async function loadRoles() {
    try {
        const res = await http.get('/admin/roles');
        roleOptions.value = res.data || [];
    } catch {
        roleOptions.value = [];
    }
}

async function loadUsers() {
    usersLoading.value = true;
    try {
        const res = await http.get('/admin/users');
        users.value = res.data || [];
    } catch {
        users.value = [];
    } finally {
        usersLoading.value = false;
    }
}

// 字段模板
const docTypes = ref([]);
const typesLoading = ref(false);
const templateDialogVisible = ref(false);
const currentType = ref(null);
const currentFields = ref([]);

// OCR
const ocrStatus = ref({});
const ocrLoading = ref(false);

const engineModeMap = { aliyun_api: '阿里云 API', local_model: '本地模型', mock: '模拟模式', offline: '离线' };

async function loadDocTypes() {
    typesLoading.value = true;
    try {
        const res = await documentApi.types();
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
    loadRoles();
    loadDocTypes();
    loadOcrStatus();
});
</script>

<style scoped>
.settings-page :deep(.el-tabs__content) { padding-top: 8px; }
.tab-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.tab-title { font-size: 14px; font-weight: 600; }
.mr-4 { margin-right: 4px; }
.text-light { color: #c0c4cc; }
.form-tip { font-size: 11px; color: #c0c4cc; margin-top: 2px; line-height: 1.4; }
.ocr-tip { margin-top: 16px; font-size: 13px; color: #606266; }
.ocr-tip ul { margin-top: 8px; padding-left: 20px; }
.ocr-tip li { margin-bottom: 4px; }
</style>
