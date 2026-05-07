<template>
  <div class="dashboard" v-loading="loading">
    <!-- 统计卡片 -->
    <el-row :gutter="16" class="stats-row">
      <el-col :span="6">
        <el-card shadow="never" class="stat-card">
          <div class="stat-icon" style="color:#409eff">📄</div>
          <div class="stat-value">{{ stats.total_this_month || 0 }}</div>
          <div class="stat-label">本月文件数</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never" class="stat-card">
          <div class="stat-icon" style="color:#e6a23c">⏳</div>
          <div class="stat-value" :style="{ color: stats.pending_count > 0 ? '#e6a23c' : '#67c23a' }">{{ stats.pending_count || 0 }}</div>
          <div class="stat-label">待处理文件</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never" class="stat-card">
          <div class="stat-icon" style="color:#67c23a">✅</div>
          <div class="stat-value" style="color:#67c23a">{{ stats.ocr_accuracy ? Number(stats.ocr_accuracy).toFixed(1) + '%' : '—' }}</div>
          <div class="stat-label">字段提取准确率</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never" class="stat-card">
          <div class="stat-icon" style="color:#909399">📊</div>
          <div class="stat-value">{{ formatNumber(stats.total_fields) }}</div>
          <div class="stat-label">已提取字段数</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16">
      <!-- 近期文件 -->
      <el-col :span="12">
        <el-card shadow="never">
          <template #header><span>近期上传文件</span></template>
          <el-table :data="recentDocs" size="small" stripe @row-click="row => $router.push(`/documents/${row.id}`)">
            <el-table-column label="编号" prop="doc_no" width="140">
              <template #default="{ row }"><span style="color:#409eff;cursor:pointer;">{{ row.doc_no }}</span></template>
            </el-table-column>
            <el-table-column label="类型" width="110">
              <template #default="{ row }">
                <span :class="['type-tag', `type-${row.document_type?.color}`]">{{ row.document_type?.icon }} {{ row.document_type?.name }}</span>
              </template>
            </el-table-column>
            <el-table-column label="文件名" prop="original_filename" min-width="150" show-overflow-tooltip />
            <el-table-column label="状态" width="80">
              <template #default="{ row }">
                <span :class="['status-dot', `status-${row.status}`]">{{ statusMap[row.status] }}</span>
              </template>
            </el-table-column>
            <el-table-column label="时间" width="140">
              <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
            </el-table-column>
          </el-table>
          <el-empty v-if="!recentDocs.length" description="暂无文件" :image-size="60" />
        </el-card>
      </el-col>

      <!-- 文件类型分布 -->
      <el-col :span="12">
        <el-card shadow="never">
          <template #header><span>本月文件类型分布</span></template>
          <div class="type-dist" v-if="stats.type_distribution?.length">
            <div v-for="item in stats.type_distribution" :key="item.id" class="dist-item">
              <div class="dist-header">
                <span :class="['type-tag', `type-${item.color}`]">{{ item.name }}</span>
                <span class="dist-count">{{ item.count }} 份</span>
              </div>
              <el-progress
                :percentage="maxCount ? Math.round(item.count / maxCount * 100) : 0"
                :stroke-width="10"
                :show-text="false"
                :color="getBarColor(item.color)"
              />
            </div>
          </div>
          <el-empty v-else description="本月暂无数据" :image-size="60" />
        </el-card>

        <!-- 快捷操作 -->
        <el-card shadow="never" class="mt-16">
          <template #header><span>快捷操作</span></template>
          <div class="quick-actions">
            <el-button type="primary" @click="$router.push('/upload')"><el-icon><Upload /></el-icon> 上传文件</el-button>
            <el-button @click="$router.push('/documents')"><el-icon><Document /></el-icon> 文件管理</el-button>
            <el-button @click="$router.push('/review')"><el-icon><EditPen /></el-icon> 人工核对</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { documentApi } from '@/api/document';

const loading = ref(true);
const stats = ref({});
const recentDocs = ref([]);

const statusMap = {
    draft: '待处理', ocr_processing: '识别中', pending_review: '待核对',
    pending_approval: '待审批', approved: '已审批', archived: '已归档', voided: '已作废',
};

const maxCount = computed(() => {
    if (!stats.value.type_distribution?.length) return 0;
    return Math.max(...stats.value.type_distribution.map(i => i.count));
});

function statusType(s) {
    return { draft: 'info', ocr_processing: 'warning', pending_review: 'warning', archived: 'success', voided: 'danger' }[s] || 'info';
}
function getTagType(c) {
    return { blue: '', green: 'success', amber: 'warning', coral: 'danger', gray: 'info' }[c] || 'info';
}
function getBarColor(c) {
    return { blue: '#409eff', green: '#67c23a', amber: '#e6a23c', coral: '#f56c6c', gray: '#909399' }[c] || '#409eff';
}
function formatNumber(n) {
    if (!n) return '0';
    return n >= 10000 ? (n / 10000).toFixed(1) + '万' : n.toLocaleString();
}
function formatDate(str) {
    if (!str) return '';
    return new Date(str).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' });
}

onMounted(async () => {
    try {
        const [statsRes, docsRes] = await Promise.all([
            documentApi.statistics(),
            documentApi.list({ per_page: 8 }),
        ]);
        stats.value = statsRes.data;
        recentDocs.value = docsRes.data;
    } finally {
        loading.value = false;
    }
});
</script>

<style scoped>
.stats-row { margin-bottom: 16px; }
.stat-card { text-align: center; }
.stat-card :deep(.el-card__body) { padding: 16px 20px; }
.stat-icon { font-size: 20px; margin-bottom: 4px; }
.stat-value { font-size: 28px; font-weight: 600; color: #303133; }
.stat-label { font-size: 12px; color: #909399; margin-top: 4px; }
.type-dist { display: flex; flex-direction: column; gap: 12px; }
.dist-item { }
.dist-header { display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 4px; }
.dist-count { color: #909399; }
.quick-actions { display: flex; gap: 10px; }
.mt-16 { margin-top: 16px; }

/* 文件类型标签 */
.type-tag { display: inline-block; font-size: 11px; padding: 2px 6px; border-radius: 4px; font-weight: 500; }
.type-blue { background: #e6f1fb; color: #185fa5; }
.type-green { background: #eaf3de; color: #3b6d11; }
.type-amber { background: #faeeda; color: #854f0b; }
.type-gray { background: #f1efe8; color: #5f5e5a; }
.type-coral { background: #faece7; color: #993c1d; }

/* 状态标识 */
.status-dot { display: inline-flex; align-items: center; gap: 4px; font-size: 11px; font-weight: 500; }
.status-dot::before { content: ''; width: 6px; height: 6px; border-radius: 50%; }
.status-draft { color: #909399; } .status-draft::before { background: #909399; }
.status-ocr_processing { color: #e6a23c; } .status-ocr_processing::before { background: #e6a23c; }
.status-pending_review { color: #e6a23c; } .status-pending_review::before { background: #e6a23c; }
.status-pending_approval { color: #409eff; } .status-pending_approval::before { background: #409eff; }
.status-archived { color: #67c23a; } .status-archived::before { background: #67c23a; }
.status-voided { color: #f56c6c; } .status-voided::before { background: #f56c6c; }
</style>
