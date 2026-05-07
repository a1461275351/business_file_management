<template>
  <div class="order-page">
    <!-- 筛选+操作栏 -->
    <el-card shadow="never" class="filter-card">
      <div class="filter-row">
        <div class="filter-left">
          <el-input v-model="keyword" placeholder="搜索订单号..." clearable size="small" style="width:200px" @keyup.enter="loadData" @clear="loadData">
            <template #prefix><el-icon><Search /></el-icon></template>
          </el-input>
          <el-select v-model="statusFilter" placeholder="状态" clearable size="small" style="width:100px" @change="loadData">
            <el-option label="草稿" value="draft" />
            <el-option label="已确认" value="confirmed" />
            <el-option label="运输中" value="shipping" />
            <el-option label="已完成" value="completed" />
          </el-select>
        </div>
        <el-button type="primary" size="small" @click="showForm = true; formData = { order_type: 'export', currency: 'USD' }">
          <el-icon><Plus /></el-icon> 新建订单
        </el-button>
      </div>
    </el-card>

    <!-- 订单列表 -->
    <el-table :data="orders" v-loading="loading" stripe size="small">
      <el-table-column label="订单号" prop="order_no" width="130">
        <template #default="{ row }"><span class="link">{{ row.order_no }}</span></template>
      </el-table-column>
      <el-table-column label="类型" width="70">
        <template #default="{ row }">
          <el-tag size="small" :type="row.order_type === 'export' ? '' : 'warning'">{{ row.order_type === 'export' ? '出口' : '进口' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="客户" min-width="150">
        <template #default="{ row }">{{ row.customer?.company_name || '—' }}</template>
      </el-table-column>
      <el-table-column label="金额" width="130">
        <template #default="{ row }">
          <span v-if="row.total_amount">{{ row.currency }} {{ Number(row.total_amount).toLocaleString() }}</span>
          <span v-else class="muted">—</span>
        </template>
      </el-table-column>
      <el-table-column label="贸易条款" prop="trade_terms" width="80" />
      <el-table-column label="目的国" prop="destination_country" width="80" />
      <el-table-column label="关联文件" width="80" align="center">
        <template #default="{ row }">
          <el-tag size="small" type="info">{{ row.documents_count || 0 }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="80">
        <template #default="{ row }">
          <span :class="['status-dot', `os-${row.status}`]">{{ orderStatusMap[row.status] }}</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="120" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" size="small" @click="editOrder(row)">编辑</el-button>
          <el-button link type="danger" size="small" @click="deleteOrder(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination-bar">
      <el-pagination v-model:current-page="page" :total="total" :page-size="20" layout="total, prev, pager, next" @current-change="loadData" />
    </div>

    <!-- 新建/编辑弹窗 -->
    <el-dialog v-model="showForm" :title="formData.id ? '编辑订单' : '新建订单'" width="600px">
      <el-form :model="formData" label-width="80px" size="small">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="订单号" required><el-input v-model="formData.order_no" placeholder="如 SO-8820" /></el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="类型">
              <el-radio-group v-model="formData.order_type">
                <el-radio label="export">出口</el-radio>
                <el-radio label="import">进口</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="客户">
              <el-select v-model="formData.customer_id" placeholder="选择客户" filterable clearable style="width:100%">
                <el-option v-for="c in customerOptions" :key="c.id" :label="c.company_name" :value="c.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="币种"><el-input v-model="formData.currency" placeholder="USD" /></el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="金额"><el-input v-model="formData.total_amount" type="number" /></el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="贸易条款"><el-input v-model="formData.trade_terms" placeholder="FOB/CIF" /></el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="付款条款"><el-input v-model="formData.payment_terms" placeholder="T/T 30days" /></el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="目的国"><el-input v-model="formData.destination_country" /></el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="备注"><el-input v-model="formData.remarks" type="textarea" :rows="2" /></el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="showForm = false">取消</el-button>
        <el-button type="primary" @click="saveOrder" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import http from '@/api/http';

const loading = ref(false);
const orders = ref([]);
const total = ref(0);
const page = ref(1);
const keyword = ref('');
const statusFilter = ref('');
const showForm = ref(false);
const saving = ref(false);
const formData = ref({});
const customerOptions = ref([]);

const orderStatusMap = { draft: '草稿', confirmed: '已确认', shipping: '运输中', completed: '已完成', cancelled: '已取消' };

async function loadData() {
    loading.value = true;
    try {
        const params = { page: page.value, per_page: 20 };
        if (keyword.value) params.keyword = keyword.value;
        if (statusFilter.value) params.status = statusFilter.value;
        const res = await http.get('/orders', { params });
        orders.value = res.data;
        total.value = res.total;
    } finally { loading.value = false; }
}

async function loadCustomers() {
    try {
        const res = await http.get('/customers/options');
        customerOptions.value = res.data;
    } catch {}
}

function editOrder(row) {
    formData.value = { ...row };
    showForm.value = true;
}

async function saveOrder() {
    saving.value = true;
    try {
        if (formData.value.id) {
            await http.put(`/orders/${formData.value.id}`, formData.value);
            ElMessage.success('订单已更新');
        } else {
            await http.post('/orders', formData.value);
            ElMessage.success('订单已创建');
        }
        showForm.value = false;
        loadData();
    } catch {} finally { saving.value = false; }
}

async function deleteOrder(row) {
    try {
        await ElMessageBox.confirm(`确定删除订单 ${row.order_no}？`, '删除', { type: 'warning' });
        await http.delete(`/orders/${row.id}`);
        ElMessage.success('已删除');
        loadData();
    } catch {}
}

onMounted(() => { loadData(); loadCustomers(); });
</script>

<style scoped>
.filter-card { margin-bottom: 16px; }
.filter-card :deep(.el-card__body) { padding: 12px 16px; }
.filter-row { display: flex; justify-content: space-between; align-items: center; }
.filter-left { display: flex; gap: 8px; }
.link { color: #409eff; cursor: pointer; font-weight: 500; }
.muted { color: #c0c4cc; }
.pagination-bar { margin-top: 16px; display: flex; justify-content: flex-end; }
.status-dot { display: inline-flex; align-items: center; gap: 4px; font-size: 12px; font-weight: 500; }
.status-dot::before { content: ''; width: 6px; height: 6px; border-radius: 50%; }
.os-draft { color: #909399; } .os-draft::before { background: #909399; }
.os-confirmed { color: #409eff; } .os-confirmed::before { background: #409eff; }
.os-shipping { color: #e6a23c; } .os-shipping::before { background: #e6a23c; }
.os-completed { color: #67c23a; } .os-completed::before { background: #67c23a; }
.os-cancelled { color: #f56c6c; } .os-cancelled::before { background: #f56c6c; }
</style>
