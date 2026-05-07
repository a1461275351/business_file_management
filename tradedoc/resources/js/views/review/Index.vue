<template>
  <div class="review-page">
    <!-- 统计卡片 -->
    <el-row :gutter="12" class="stats-row">
      <el-col :span="6">
        <el-card shadow="never" class="stat-card">
          <div class="stat-value" style="color:#f56c6c">{{ stats.urgent || 0 }}</div>
          <div class="stat-label">紧急待核对</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never" class="stat-card">
          <div class="stat-value">{{ stats.pending || 0 }}</div>
          <div class="stat-label">待分配</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never" class="stat-card">
          <div class="stat-value" style="color:#e6a23c">{{ stats.in_progress || 0 }}</div>
          <div class="stat-label">进行中</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never" class="stat-card">
          <div class="stat-value" style="color:#67c23a">{{ stats.completed_today || 0 }}</div>
          <div class="stat-label">今日已完成</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 筛选 -->
    <div class="filter-row">
      <el-radio-group v-model="filters.status" size="small" @change="loadData">
        <el-radio-button label="">全部</el-radio-button>
        <el-radio-button label="pending">待分配</el-radio-button>
        <el-radio-button label="in_progress">进行中</el-radio-button>
        <el-radio-button label="completed">已完成</el-radio-button>
      </el-radio-group>
      <el-select v-model="filters.priority" placeholder="优先级" clearable size="small" style="width:100px" @change="loadData">
        <el-option label="紧急" value="urgent" />
        <el-option label="中" value="medium" />
        <el-option label="普通" value="normal" />
      </el-select>
    </div>

    <!-- 任务列表 -->
    <el-table :data="tasks" v-loading="loading" stripe size="small">
      <el-table-column label="文件编号" width="140">
        <template #default="{ row }">
          <span class="link" @click="$router.push(`/documents/${row.document_id}`)">{{ row.document?.doc_no }}</span>
        </template>
      </el-table-column>
      <el-table-column label="文件类型" width="100">
        <template #default="{ row }">
          <el-tag size="small" :type="tagType(row.document?.document_type?.color)">
            {{ row.document?.document_type?.name }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="待确认字段" min-width="180">
        <template #default="{ row }">{{ (row.field_ids || []).length }} 个字段</template>
      </el-table-column>
      <el-table-column label="优先级" width="80">
        <template #default="{ row }">
          <el-tag size="small" :type="priorityType(row.priority)">{{ priorityMap[row.priority] }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="分配给" width="100">
        <template #default="{ row }">{{ row.assignee?.real_name || '未分配' }}</template>
      </el-table-column>
      <el-table-column label="等待时长" width="100">
        <template #default="{ row }">{{ timeAgo(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="状态" width="80">
        <template #default="{ row }">
          <el-tag size="small" :type="statusType(row.status)">{{ statusMap[row.status] }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="100" fixed="right">
        <template #default="{ row }">
          <el-button v-if="row.status !== 'completed'" link type="primary" size="small" @click="openReview(row)">核对</el-button>
          <el-button v-else link size="small" @click="$router.push(`/documents/${row.document_id}`)">查看</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination-bar">
      <el-pagination v-model:current-page="page" :total="total" :page-size="20" layout="total, prev, pager, next" @current-change="loadData" />
    </div>

    <!-- 核对弹窗 -->
    <el-dialog v-model="reviewDialogVisible" title="字段核对" width="700px" :close-on-click-modal="false">
      <div v-if="currentTask" v-loading="detailLoading">
        <div class="review-doc-info">
          <span>{{ currentTask.task?.document?.doc_no }}</span>
          <el-tag size="small" class="ml-8">{{ currentTask.task?.document?.document_type?.name }}</el-tag>
        </div>
        <el-table :data="currentTask.fields || []" size="small" stripe class="review-table">
          <el-table-column label="字段" width="100">
            <template #default="{ row }">{{ row.template?.field_name || row.field_key }}</template>
          </el-table-column>
          <el-table-column label="识别值" min-width="180">
            <template #default="{ row }">
              <el-input v-model="fieldEdits[row.id]" size="small" :class="{ 'low-conf': row.confidence < 80 }" />
            </template>
          </el-table-column>
          <el-table-column label="置信度" width="80" align="center">
            <template #default="{ row }">
              <span :style="{ color: row.confidence >= 80 ? '#67c23a' : '#f56c6c', fontWeight: 500 }">{{ row.confidence }}%</span>
            </template>
          </el-table-column>
          <el-table-column label="必填" width="50" align="center">
            <template #default="{ row }">
              <span v-if="row.template?.is_required" style="color:#f56c6c">*</span>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <template #footer>
        <el-button @click="handleSkip" :loading="submitting">跳过</el-button>
        <el-button type="primary" @click="handleConfirm" :loading="submitting">全部确认并提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import { reviewApi } from '@/api/review';

const loading = ref(false);
const tasks = ref([]);
const total = ref(0);
const page = ref(1);
const stats = ref({});
const filters = reactive({ status: '', priority: '' });

// 核对弹窗
const reviewDialogVisible = ref(false);
const detailLoading = ref(false);
const currentTask = ref(null);
const fieldEdits = ref({});
const submitting = ref(false);

const priorityMap = { urgent: '紧急', medium: '中', normal: '普通' };
const statusMap = { pending: '待分配', assigned: '已分配', in_progress: '进行中', completed: '已完成' };

function tagType(c) { return { blue: '', green: 'success', amber: 'warning', coral: 'danger', gray: 'info' }[c] || 'info'; }
function priorityType(p) { return { urgent: 'danger', medium: 'warning', normal: 'info' }[p] || 'info'; }
function statusType(s) { return { pending: 'info', assigned: '', in_progress: 'warning', completed: 'success' }[s] || 'info'; }

function timeAgo(dateStr) {
    if (!dateStr) return '';
    const diff = Date.now() - new Date(dateStr).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 60) return `${mins}分钟`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}小时`;
    return `${Math.floor(hours / 24)}天`;
}

async function loadData() {
    loading.value = true;
    try {
        const params = { ...filters, page: page.value, per_page: 20 };
        Object.keys(params).forEach(k => { if (!params[k]) delete params[k]; });
        const res = await reviewApi.list(params);
        tasks.value = res.data;
        total.value = res.total;
    } finally {
        loading.value = false;
    }
}

async function loadStats() {
    try {
        const res = await reviewApi.statistics();
        stats.value = res.data;
    } catch {}
}

async function openReview(row) {
    reviewDialogVisible.value = true;
    detailLoading.value = true;
    try {
        const res = await reviewApi.detail(row.id);
        currentTask.value = res.data;
        // 初始化编辑值
        fieldEdits.value = {};
        (res.data.fields || []).forEach(f => {
            fieldEdits.value[f.id] = f.field_value || '';
        });
    } finally {
        detailLoading.value = false;
    }
}

async function handleConfirm() {
    if (!currentTask.value) return;
    submitting.value = true;
    try {
        const fields = Object.entries(fieldEdits.value).map(([id, value]) => ({
            field_id: parseInt(id),
            value,
        }));
        await reviewApi.confirm(currentTask.value.task.id, fields);
        ElMessage.success('核对完成');
        reviewDialogVisible.value = false;
        loadData();
        loadStats();
    } catch {} finally {
        submitting.value = false;
    }
}

async function handleSkip() {
    if (!currentTask.value) return;
    submitting.value = true;
    try {
        await reviewApi.skip(currentTask.value.task.id);
        ElMessage.info('已跳过');
        reviewDialogVisible.value = false;
        loadData();
    } catch {} finally {
        submitting.value = false;
    }
}

onMounted(() => {
    loadData();
    loadStats();
});
</script>

<style scoped>
.stats-row { margin-bottom: 16px; }
.stat-card { text-align: center; }
.stat-card :deep(.el-card__body) { padding: 16px; }
.stat-value { font-size: 28px; font-weight: 600; color: #303133; }
.stat-label { font-size: 12px; color: #909399; margin-top: 4px; }
.filter-row { display: flex; gap: 12px; margin-bottom: 16px; }
.link { color: #409eff; cursor: pointer; }
.link:hover { text-decoration: underline; }
.pagination-bar { margin-top: 16px; display: flex; justify-content: flex-end; }
.review-doc-info { margin-bottom: 12px; font-size: 14px; font-weight: 500; }
.ml-8 { margin-left: 8px; }
.review-table :deep(.low-conf .el-input__wrapper) { border-color: #f56c6c; }
</style>
