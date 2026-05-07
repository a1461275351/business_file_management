<template>
  <div class="reports-page" v-loading="loading">
    <!-- 筛选 -->
    <el-card shadow="never" class="filter-card">
      <div class="filter-row">
        <el-date-picker v-model="dateRange" type="monthrange" size="small" start-placeholder="开始月份" end-placeholder="结束月份" format="YYYY-MM" value-format="YYYY-MM" @change="loadData" />
        <el-button type="primary" size="small" @click="loadData"><el-icon><Refresh /></el-icon> 刷新</el-button>
      </div>
    </el-card>

    <!-- 统计概览 -->
    <el-row :gutter="12" class="stats-row">
      <el-col :span="6">
        <el-card shadow="never" class="stat-card">
          <div class="stat-label">文件总数</div>
          <div class="stat-value">{{ report.total_documents || 0 }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never" class="stat-card">
          <div class="stat-label">已归档</div>
          <div class="stat-value" style="color:#67c23a">{{ report.archived_count || 0 }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never" class="stat-card">
          <div class="stat-label">字段提取准确率</div>
          <div class="stat-value">{{ report.avg_confidence ? report.avg_confidence + '%' : '—' }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never" class="stat-card">
          <div class="stat-label">提取字段数</div>
          <div class="stat-value">{{ report.total_fields || 0 }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16">
      <!-- 文件类型分布 -->
      <el-col :span="12">
        <el-card shadow="never">
          <template #header><span>文件类型分布</span></template>
          <div class="type-list" v-if="report.type_distribution?.length">
            <div v-for="item in report.type_distribution" :key="item.name" class="type-item">
              <div class="type-header">
                <span>{{ item.name }}</span>
                <span class="type-count">{{ item.count }} 份</span>
              </div>
              <el-progress :percentage="maxTypeCount ? Math.round(item.count / maxTypeCount * 100) : 0" :stroke-width="8" :show-text="false" />
            </div>
          </div>
          <el-empty v-else description="暂无数据" :image-size="60" />
        </el-card>
      </el-col>

      <!-- 状态分布 -->
      <el-col :span="12">
        <el-card shadow="never">
          <template #header><span>文件状态分布</span></template>
          <div class="status-list" v-if="report.status_distribution?.length">
            <div v-for="item in report.status_distribution" :key="item.status" class="status-item">
              <el-tag :type="statusType(item.status)" size="small">{{ statusMap[item.status] }}</el-tag>
              <span class="status-count">{{ item.count }} 份</span>
            </div>
          </div>
          <el-empty v-else description="暂无数据" :image-size="60" />
        </el-card>
      </el-col>
    </el-row>

    <!-- 月度趋势 -->
    <el-card shadow="never" class="mt-16" v-if="report.monthly_trend?.length">
      <template #header><span>月度文件上传趋势</span></template>
      <div class="trend-chart">
        <div v-for="m in report.monthly_trend" :key="m.month" class="trend-bar-wrap">
          <div class="trend-bar" :style="{ height: maxMonthly ? (m.count / maxMonthly * 120) + 'px' : '0' }"></div>
          <div class="trend-label">{{ m.month }}</div>
          <div class="trend-count">{{ m.count }}</div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import http from '@/api/http';

const loading = ref(false);
const dateRange = ref([]);
const report = ref({});

const statusMap = {
    draft: '草稿', ocr_processing: 'OCR中', pending_review: '待核对',
    pending_approval: '待审核', archived: '已归档', voided: '已作废',
};

function statusType(s) {
    return { draft: 'info', ocr_processing: 'warning', pending_review: 'warning', pending_approval: '', archived: 'success', voided: 'danger' }[s] || 'info';
}

const maxTypeCount = computed(() => {
    if (!report.value.type_distribution?.length) return 0;
    return Math.max(...report.value.type_distribution.map(i => i.count));
});

const maxMonthly = computed(() => {
    if (!report.value.monthly_trend?.length) return 0;
    return Math.max(...report.value.monthly_trend.map(i => i.count));
});

async function loadData() {
    loading.value = true;
    try {
        const params = {};
        if (dateRange.value?.length === 2) {
            params.date_from = dateRange.value[0];
            params.date_to = dateRange.value[1];
        }
        const res = await http.get('/documents/reports', { params });
        report.value = res.data;
    } catch {
        // 如果接口还没实现，用统计接口的数据
        try {
            const res = await http.get('/documents/statistics');
            report.value = {
                total_documents: res.data.total_this_month,
                archived_count: 0,
                avg_confidence: res.data.ocr_accuracy,
                total_fields: res.data.total_fields,
                type_distribution: res.data.type_distribution,
                status_distribution: [],
                monthly_trend: [],
            };
        } catch {}
    } finally {
        loading.value = false;
    }
}

onMounted(loadData);
</script>

<style scoped>
.filter-card { margin-bottom: 16px; }
.filter-card :deep(.el-card__body) { padding: 12px 16px; }
.filter-row { display: flex; gap: 12px; align-items: center; }
.stats-row { margin-bottom: 16px; }
.stat-card { text-align: center; }
.stat-card :deep(.el-card__body) { padding: 16px; }
.stat-label { font-size: 12px; color: #909399; margin-bottom: 6px; }
.stat-value { font-size: 26px; font-weight: 600; color: #303133; }
.type-list { display: flex; flex-direction: column; gap: 12px; }
.type-header { display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 4px; }
.type-count { color: #909399; }
.status-list { display: flex; flex-direction: column; gap: 10px; }
.status-item { display: flex; align-items: center; gap: 12px; }
.status-count { font-size: 14px; font-weight: 500; }
.mt-16 { margin-top: 16px; }
.trend-chart { display: flex; align-items: flex-end; gap: 8px; height: 160px; padding-top: 20px; }
.trend-bar-wrap { flex: 1; text-align: center; display: flex; flex-direction: column; align-items: center; justify-content: flex-end; }
.trend-bar { width: 32px; background: #409eff; border-radius: 4px 4px 0 0; min-height: 4px; transition: height 0.3s; }
.trend-label { font-size: 11px; color: #909399; margin-top: 6px; }
.trend-count { font-size: 12px; font-weight: 500; color: #303133; }
</style>
