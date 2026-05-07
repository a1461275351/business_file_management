<template>
  <div class="customer-page">
    <el-card shadow="never" class="filter-card">
      <div class="filter-row">
        <div class="filter-left">
          <el-input v-model="keyword" placeholder="搜索公司名/联系人..." clearable size="small" style="width:220px" @keyup.enter="loadData" @clear="loadData">
            <template #prefix><el-icon><Search /></el-icon></template>
          </el-input>
          <el-select v-model="typeFilter" placeholder="类型" clearable size="small" style="width:100px" @change="loadData">
            <el-option label="客户" value="customer" />
            <el-option label="供应商" value="supplier" />
            <el-option label="双重" value="both" />
          </el-select>
        </div>
        <el-button type="primary" size="small" @click="showForm = true; formData = { type: 'customer' }">
          <el-icon><Plus /></el-icon> 新建客户
        </el-button>
      </div>
    </el-card>

    <el-table :data="customers" v-loading="loading" stripe size="small">
      <el-table-column label="公司名称" min-width="180">
        <template #default="{ row }">
          <div><span class="link">{{ row.company_name }}</span></div>
          <div class="sub-text" v-if="row.company_name_en">{{ row.company_name_en }}</div>
        </template>
      </el-table-column>
      <el-table-column label="简称" prop="short_name" width="80" />
      <el-table-column label="类型" width="70">
        <template #default="{ row }">
          <el-tag size="small" :type="typeTagMap[row.type]">{{ typeMap[row.type] }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="国家" prop="country" width="80" />
      <el-table-column label="联系人" prop="contact_person" width="80" />
      <el-table-column label="电话" prop="contact_phone" width="120" />
      <el-table-column label="邮箱" prop="contact_email" width="160" show-overflow-tooltip />
      <el-table-column label="订单数" width="70" align="center">
        <template #default="{ row }"><el-tag size="small" type="info">{{ row.orders_count || 0 }}</el-tag></template>
      </el-table-column>
      <el-table-column label="操作" width="120" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" size="small" @click="editCustomer(row)">编辑</el-button>
          <el-button link type="danger" size="small" @click="deleteCustomer(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination-bar">
      <el-pagination v-model:current-page="page" :total="total" :page-size="20" layout="total, prev, pager, next" @current-change="loadData" />
    </div>

    <!-- 新建/编辑弹窗 -->
    <el-dialog v-model="showForm" :title="formData.id ? '编辑客户' : '新建客户'" width="650px">
      <el-form :model="formData" label-width="80px" size="small">
        <el-row :gutter="16">
          <el-col :span="16">
            <el-form-item label="公司名称" required><el-input v-model="formData.company_name" /></el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="类型">
              <el-select v-model="formData.type" style="width:100%">
                <el-option label="客户" value="customer" />
                <el-option label="供应商" value="supplier" />
                <el-option label="双重" value="both" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="英文名"><el-input v-model="formData.company_name_en" /></el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="简称"><el-input v-model="formData.short_name" /></el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="国家"><el-input v-model="formData.country" /></el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="联系人"><el-input v-model="formData.contact_person" /></el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="电话"><el-input v-model="formData.contact_phone" /></el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="邮箱"><el-input v-model="formData.contact_email" /></el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="地址"><el-input v-model="formData.address" /></el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="开户行"><el-input v-model="formData.bank_name" /></el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="银行账号"><el-input v-model="formData.bank_account" /></el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="SWIFT"><el-input v-model="formData.swift_code" /></el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="税号"><el-input v-model="formData.tax_id" /></el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="备注"><el-input v-model="formData.remarks" type="textarea" :rows="2" /></el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="showForm = false">取消</el-button>
        <el-button type="primary" @click="saveCustomer" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import http from '@/api/http';

const loading = ref(false);
const customers = ref([]);
const total = ref(0);
const page = ref(1);
const keyword = ref('');
const typeFilter = ref('');
const showForm = ref(false);
const saving = ref(false);
const formData = ref({});

const typeMap = { customer: '客户', supplier: '供应商', both: '双重' };
const typeTagMap = { customer: '', supplier: 'warning', both: 'success' };

async function loadData() {
    loading.value = true;
    try {
        const params = { page: page.value, per_page: 20 };
        if (keyword.value) params.keyword = keyword.value;
        if (typeFilter.value) params.type = typeFilter.value;
        const res = await http.get('/customers', { params });
        customers.value = res.data;
        total.value = res.total;
    } finally { loading.value = false; }
}

function editCustomer(row) {
    formData.value = { ...row };
    showForm.value = true;
}

async function saveCustomer() {
    saving.value = true;
    try {
        if (formData.value.id) {
            await http.put(`/customers/${formData.value.id}`, formData.value);
            ElMessage.success('客户已更新');
        } else {
            await http.post('/customers', formData.value);
            ElMessage.success('客户已创建');
        }
        showForm.value = false;
        loadData();
    } catch {} finally { saving.value = false; }
}

async function deleteCustomer(row) {
    try {
        await ElMessageBox.confirm(`确定删除客户「${row.company_name}」？`, '删除', { type: 'warning' });
        await http.delete(`/customers/${row.id}`);
        ElMessage.success('已删除');
        loadData();
    } catch {}
}

onMounted(loadData);
</script>

<style scoped>
.filter-card { margin-bottom: 16px; }
.filter-card :deep(.el-card__body) { padding: 12px 16px; }
.filter-row { display: flex; justify-content: space-between; align-items: center; }
.filter-left { display: flex; gap: 8px; }
.link { color: #409eff; cursor: pointer; font-weight: 500; }
.sub-text { font-size: 11px; color: #909399; }
.pagination-bar { margin-top: 16px; display: flex; justify-content: flex-end; }
</style>
