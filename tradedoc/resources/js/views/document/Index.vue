<template>
  <div class="doc-page">
    <!-- 筛选栏 -->
    <el-card shadow="never" class="filter-card">
      <div class="filter-row">
        <div class="filter-tags">
          <el-tag
            v-for="type in [{ id: null, name: '全部' }, ...docTypes]"
            :key="type.id ?? 'all'"
            :effect="filters.document_type_id === type.id ? 'dark' : 'plain'"
            class="filter-tag"
            @click="filters.document_type_id = type.id; loadData()"
          >
            {{ type.name }}
          </el-tag>
        </div>
        <div class="filter-actions">
          <el-input v-model="filters.keyword" placeholder="搜索文件编号、文件名..." clearable size="small" style="width: 220px" @clear="loadData" @keyup.enter="loadData">
            <template #prefix><el-icon><Search /></el-icon></template>
          </el-input>
          <el-select v-model="filters.status" placeholder="状态" clearable size="small" style="width: 120px" @change="loadData">
            <el-option label="待处理" value="draft" />
            <el-option label="识别中" value="ocr_processing" />
            <el-option label="待核对" value="pending_review" />
            <el-option label="待审核" value="pending_approval" />
            <el-option label="已归档" value="archived" />
          </el-select>
          <el-button size="small" @click="exportAll"><el-icon><Download /></el-icon> 导出</el-button>
          <el-button type="primary" size="small" @click="$router.push('/upload')">
            <el-icon><Upload /></el-icon>上传文件
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- 批量操作栏 -->
    <div class="batch-bar" v-if="selectedIds.length > 0">
      <span class="batch-info">已选 {{ selectedIds.length }} 项</span>
      <el-button size="small" @click="batchArchive"><el-icon><FolderChecked /></el-icon> 批量归档</el-button>
      <el-button size="small" @click="batchExport"><el-icon><Download /></el-icon> 导出 Excel</el-button>
      <el-button size="small" type="danger" @click="batchDelete"><el-icon><Delete /></el-icon> 批量删除</el-button>
      <el-button size="small" @click="selectedIds = []">取消选择</el-button>
    </div>

    <!-- 文件列表 -->
    <el-table :data="documents" v-loading="loading" stripe class="doc-table" @row-click="goDetail" @selection-change="rows => selectedIds = rows.map(r => r.id)">
      <el-table-column type="selection" width="40" />
      <el-table-column label="文件编号" prop="doc_no" width="150">
        <template #default="{ row }">
          <span class="doc-no">{{ row.doc_no }}</span>
        </template>
      </el-table-column>
      <el-table-column label="文件类型" width="120">
        <template #default="{ row }">
          <span :class="['type-tag', `type-${row.document_type?.color}`]">
            {{ row.document_type?.icon }} {{ row.document_type?.name }}
          </span>
        </template>
      </el-table-column>
      <el-table-column label="文件名" prop="original_filename" min-width="200" show-overflow-tooltip />
      <el-table-column label="关联订单" width="120">
        <template #default="{ row }">{{ row.order?.order_no || '—' }}</template>
      </el-table-column>
      <el-table-column label="客户/供应商" width="150">
        <template #default="{ row }">{{ row.customer?.company_name || '—' }}</template>
      </el-table-column>
      <el-table-column label="金额" width="120">
        <template #default="{ row }">
          <span v-if="row.total_amount">{{ row.currency }} {{ Number(row.total_amount).toLocaleString() }}</span>
          <span v-else class="text-muted">—</span>
        </template>
      </el-table-column>
      <el-table-column label="上传时间" width="160">
        <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="上传人" width="80">
        <template #default="{ row }">{{ row.uploader?.real_name || '—' }}</template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <span :class="['status-dot', `status-${row.status}`]">{{ statusMap[row.status] || row.status }}</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="80" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" size="small" @click.stop="goDetail(row)">查看</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <div class="pagination-bar">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.perPage"
        :total="pagination.total"
        :page-sizes="[20, 50, 100]"
        layout="total, sizes, prev, pager, next"
        @current-change="loadData"
        @size-change="loadData"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import { documentApi } from '@/api/document';
import http from '@/api/http';

const router = useRouter();
const loading = ref(false);
const documents = ref([]);
const docTypes = ref([]);
const selectedIds = ref([]);

const filters = reactive({
    document_type_id: null,
    status: null,
    keyword: '',
});

const pagination = reactive({ page: 1, perPage: 20, total: 0 });

const statusMap = {
    draft: '待处理',
    ocr_processing: '识别中',
    pending_review: '待核对',
    pending_approval: '待审批',
    approved: '已审批',
    archived: '已归档',
    voided: '已作废',
};

function statusType(status) {
    const map = { draft: 'info', ocr_processing: 'warning', pending_review: 'warning', pending_approval: '', archived: 'success', voided: 'danger' };
    return map[status] || 'info';
}

function getTagType(color) {
    const map = { blue: '', green: 'success', amber: 'warning', coral: 'danger', gray: 'info' };
    return map[color] || 'info';
}

function formatDate(str) {
    if (!str) return '';
    return new Date(str).toLocaleString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' });
}

function goDetail(row) {
    router.push(`/documents/${row.id}`);
}

async function loadData() {
    loading.value = true;
    try {
        const params = {
            ...filters,
            page: pagination.page,
            per_page: pagination.perPage,
        };
        // 移除空值
        Object.keys(params).forEach(k => { if (!params[k]) delete params[k]; });

        const res = await documentApi.list(params);
        documents.value = res.data;
        pagination.total = res.total;
    } finally {
        loading.value = false;
    }
}

function exportAll() {
    const params = new URLSearchParams();
    if (filters.document_type_id) params.set('document_type_id', filters.document_type_id);
    if (filters.status) params.set('status', filters.status);
    const token = localStorage.getItem('token');
    window.open(`/api/v1/documents/export?${params.toString()}&token=${token}`, '_blank');
}

function batchExport() {
    const token = localStorage.getItem('token');
    const ids = selectedIds.value.join(',');
    window.open(`/api/v1/documents/export?ids=${ids}&token=${token}`, '_blank');
}

async function batchArchive() {
    try {
        await ElMessageBox.confirm(`确定将 ${selectedIds.value.length} 个文件归档？`, '批量归档');
        for (const id of selectedIds.value) {
            await documentApi.changeStatus(id, 'archived').catch(() => {});
        }
        ElMessage.success('批量归档完成');
        selectedIds.value = [];
        loadData();
    } catch {}
}

async function batchDelete() {
    try {
        await ElMessageBox.confirm(`确定删除 ${selectedIds.value.length} 个文件？此操作不可恢复。`, '批量删除', { type: 'warning' });
        for (const id of selectedIds.value) {
            await documentApi.delete(id).catch(() => {});
        }
        ElMessage.success('批量删除完成');
        selectedIds.value = [];
        loadData();
    } catch {}
}

onMounted(async () => {
    const typesRes = await documentApi.types();
    docTypes.value = typesRes.data;
    loadData();
});
</script>

<style scoped>
.filter-card { margin-bottom: 16px; }
.filter-card :deep(.el-card__body) { padding: 12px 16px; }
.filter-row { display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap; }
.filter-tags { display: flex; gap: 6px; flex-wrap: wrap; }
.filter-tag { cursor: pointer; }
.filter-actions { display: flex; gap: 8px; align-items: center; }
.doc-table { cursor: pointer; }
.doc-no { font-weight: 500; color: #409eff; }
.text-muted { color: #c0c4cc; }
.batch-bar { margin-bottom: 12px; padding: 10px 16px; background: #ecf5ff; border-radius: 6px; display: flex; align-items: center; gap: 10px; }
.batch-info { font-size: 13px; color: #409eff; font-weight: 500; }
.pagination-bar { margin-top: 16px; display: flex; justify-content: flex-end; }

/* 文件类型标签 */
.type-tag { display: inline-block; font-size: 12px; padding: 2px 8px; border-radius: 4px; font-weight: 500; white-space: nowrap; }
.type-blue { background: #e6f1fb; color: #185fa5; }
.type-green { background: #eaf3de; color: #3b6d11; }
.type-amber { background: #faeeda; color: #854f0b; }
.type-gray { background: #f1efe8; color: #5f5e5a; }
.type-coral { background: #faece7; color: #993c1d; }

/* 状态标识 */
.status-dot { display: inline-flex; align-items: center; gap: 5px; font-size: 12px; font-weight: 500; }
.status-dot::before { content: ''; width: 7px; height: 7px; border-radius: 50%; display: inline-block; }
.status-draft { color: #909399; }
.status-draft::before { background: #909399; }
.status-ocr_processing { color: #e6a23c; }
.status-ocr_processing::before { background: #e6a23c; animation: pulse 1.5s infinite; }
.status-pending_review { color: #e6a23c; }
.status-pending_review::before { background: #e6a23c; }
.status-pending_approval { color: #409eff; }
.status-pending_approval::before { background: #409eff; }
.status-approved { color: #67c23a; }
.status-approved::before { background: #67c23a; }
.status-archived { color: #67c23a; }
.status-archived::before { background: #67c23a; }
.status-voided { color: #f56c6c; }
.status-voided::before { background: #f56c6c; }

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.3; }
}
</style>
