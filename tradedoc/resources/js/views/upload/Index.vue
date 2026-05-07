<template>
  <div class="upload-page">
    <!-- 拖拽上传区域 -->
    <el-upload
      ref="uploadRef"
      drag
      multiple
      :auto-upload="false"
      :on-change="handleFileChange"
      :on-remove="handleFileRemove"
      :file-list="fileList"
      :accept="'.pdf,.jpg,.jpeg,.png,.xlsx,.xls,.doc,.docx,.tiff,.tif'"
      class="upload-zone"
    >
      <el-icon class="el-icon--upload" :size="48"><UploadFilled /></el-icon>
      <div class="el-upload__text">
        拖拽文件至此，或 <em>点击选择文件</em>
      </div>
      <template #tip>
        <div class="el-upload__tip">
          支持 PDF、JPG、PNG、Excel、Word — 单文件最大 50MB，一次最多 50 个文件
        </div>
      </template>
    </el-upload>

    <!-- 选择文件类型（多选） -->
    <div class="type-section" v-if="fileList.length > 0">
      <h3 class="section-title">
        选择文件类型（AI 将按模板提取字段，可多选）
        <span class="selected-count" v-if="selectedTypeIds.length > 0">已选 {{ selectedTypeIds.length }} 种</span>
      </h3>
      <div class="type-grid">
        <div
          v-for="type in docTypes"
          :key="type.id"
          :class="['type-card', { active: selectedTypeIds.includes(type.id) }]"
          @click="toggleType(type.id)"
        >
          <div class="type-check" v-if="selectedTypeIds.includes(type.id)">
            <el-icon color="#409eff" :size="16"><CircleCheck /></el-icon>
          </div>
          <span class="type-icon">{{ type.icon }}</span>
          <div class="type-name">{{ type.name }}</div>
          <div class="type-name-en">{{ type.name_en }}</div>
        </div>
      </div>
      <div class="type-tip">
        <el-icon><InfoFilled /></el-icon>
        一个文件中包含多种单据时，请选择所有涉及的类型，系统将逐一识别提取
      </div>
    </div>

    <!-- 关联订单/客户 -->
    <div class="relate-section" v-if="fileList.length > 0">
      <el-row :gutter="16">
        <el-col :span="12">
          <span class="relate-label">关联订单（可选）</span>
          <el-select v-model="relatedOrderId" placeholder="选择订单..." filterable clearable size="small" style="width:100%">
            <el-option v-for="o in orderOptions" :key="o.id" :label="o.order_no" :value="o.id" />
          </el-select>
        </el-col>
        <el-col :span="12">
          <span class="relate-label">关联客户（可选）</span>
          <el-select v-model="relatedCustomerId" placeholder="选择客户..." filterable clearable size="small" style="width:100%">
            <el-option v-for="c in customerOptions" :key="c.id" :label="c.company_name" :value="c.id" />
          </el-select>
        </el-col>
      </el-row>
    </div>

    <!-- 已选文件列表 -->
    <div class="file-section" v-if="fileList.length > 0">
      <div class="section-header">
        <h3 class="section-title">待上传文件（{{ fileList.length }} 个）</h3>
        <el-button size="small" @click="clearFiles">清空</el-button>
      </div>
      <el-table :data="fileList" size="small" stripe>
        <el-table-column label="文件名" prop="name" min-width="200" />
        <el-table-column label="大小" width="100">
          <template #default="{ row }">{{ formatSize(row.size) }}</template>
        </el-table-column>
        <el-table-column label="类型" width="80">
          <template #default="{ row }">{{ getFileExt(row.name) }}</template>
        </el-table-column>
        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <el-tag v-if="row.status === 'success'" type="success" size="small">已上传</el-tag>
            <el-tag v-else-if="row.status === 'uploading'" type="warning" size="small">上传中</el-tag>
            <el-tag v-else-if="row.status === 'fail'" type="danger" size="small">失败</el-tag>
            <el-tag v-else type="info" size="small">待上传</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 上传进度 -->
    <div class="progress-section" v-if="uploading">
      <el-progress :percentage="uploadProgress" :status="uploadProgress === 100 ? 'success' : ''" />
      <p class="progress-text">{{ uploadStatusText }}</p>
    </div>

    <!-- 操作按钮 -->
    <div class="action-bar" v-if="fileList.length > 0">
      <el-button type="primary" size="large" :loading="uploading" :disabled="selectedTypeIds.length === 0" @click="handleUpload">
        <el-icon><Upload /></el-icon>
        确认上传并智能提取
      </el-button>
      <el-button size="large" @click="clearFiles">取消</el-button>
      <span v-if="selectedTypeIds.length === 0" class="tip-text">请先选择至少一种文件类型</span>
    </div>

    <!-- 最近上传记录 -->
    <div class="recent-section" v-if="recentUploads.length > 0">
      <h3 class="section-title">本次上传记录</h3>
      <el-table :data="recentUploads" size="small" stripe>
        <el-table-column label="文件编号" prop="doc_no" width="160" />
        <el-table-column label="文件名" prop="original_filename" min-width="200" />
        <el-table-column label="类型" width="120">
          <template #default="{ row }">
            <el-tag size="small" :type="getTagType(row.document_type?.color)">{{ row.document_type?.name }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <el-tag size="small" type="warning">{{ statusMap[row.status] || row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="$router.push(`/documents/${row.id}`)">查看</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import { documentApi } from '@/api/document';
import http from '@/api/http';

const uploadRef = ref(null);
const docTypes = ref([]);
const selectedTypeIds = ref([]);
const fileList = ref([]);
const uploading = ref(false);
const uploadProgress = ref(0);
const uploadStatusText = ref('');
const recentUploads = ref([]);
const relatedOrderId = ref(null);
const relatedCustomerId = ref(null);
const orderOptions = ref([]);
const customerOptions = ref([]);

const statusMap = {
    draft: '草稿',
    ocr_processing: '识别中',
    pending_review: '待核对',
    pending_approval: '待审核',
    archived: '已归档',
};

onMounted(async () => {
    const [typesRes, ordersRes, customersRes] = await Promise.all([
        documentApi.types(),
        http.get('/orders/options').catch(() => ({ data: [] })),
        http.get('/customers/options').catch(() => ({ data: [] })),
    ]);
    docTypes.value = typesRes.data;
    orderOptions.value = ordersRes.data;
    customerOptions.value = customersRes.data;
});

function handleFileChange(file, list) {
    fileList.value = list;
}

function handleFileRemove(file, list) {
    fileList.value = list;
}

function toggleType(id) {
    const idx = selectedTypeIds.value.indexOf(id);
    if (idx === -1) {
        selectedTypeIds.value.push(id);
    } else {
        selectedTypeIds.value.splice(idx, 1);
    }
}

function clearFiles() {
    fileList.value = [];
    selectedTypeIds.value = [];
    uploadProgress.value = 0;
    uploadRef.value?.clearFiles();
}

function formatSize(bytes) {
    if (!bytes) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return (bytes / Math.pow(k, i)).toFixed(1) + ' ' + sizes[i];
}

function getFileExt(name) {
    return name?.split('.').pop()?.toUpperCase() || '';
}

function getTagType(color) {
    const map = { blue: '', green: 'success', amber: 'warning', coral: 'danger', gray: 'info' };
    return map[color] || 'info';
}

async function handleUpload() {
    if (selectedTypeIds.value.length === 0) {
        ElMessage.warning('请先选择至少一种文件类型');
        return;
    }

    uploading.value = true;
    uploadProgress.value = 0;
    const rawFiles = fileList.value.map(f => f.raw);
    const totalTasks = rawFiles.length * selectedTypeIds.value.length;
    let completed = 0;

    uploadStatusText.value = `正在上传... 共 ${rawFiles.length} 个文件 x ${selectedTypeIds.value.length} 种类型`;

    try {
        // 每个文件 x 每种选中类型 分别创建上传记录
        for (const file of rawFiles) {
            for (const typeId of selectedTypeIds.value) {
                const formData = new FormData();
                formData.append('file', file);
                formData.append('document_type_id', typeId);
                if (relatedOrderId.value) formData.append('order_id', relatedOrderId.value);
                if (relatedCustomerId.value) formData.append('customer_id', relatedCustomerId.value);

                const res = await documentApi.upload(formData, (e) => {
                    const fileProgress = Math.round((e.loaded / e.total) * 100);
                    uploadProgress.value = Math.round((completed * 100 + fileProgress) / totalTasks);
                });

                recentUploads.value.unshift(res.data.document);
                completed++;
                uploadProgress.value = Math.round((completed / totalTasks) * 100);
            }
        }

        uploadStatusText.value = `上传完成，共创建 ${completed} 条记录，已自动提取字段`;
        ElMessage.success(`上传成功，共 ${completed} 条记录`);
        fileList.value = [];
        uploadRef.value?.clearFiles();
    } catch (err) {
        uploadStatusText.value = `上传中断，已完成 ${completed}/${totalTasks}`;
    } finally {
        uploading.value = false;
    }
}
</script>

<style scoped>
.upload-page { max-width: 900px; }
.upload-zone { width: 100%; }
.upload-zone :deep(.el-upload-dragger) { width: 100%; padding: 40px 20px; }
.section-title { font-size: 14px; font-weight: 600; color: #333; margin-bottom: 12px; }
.type-section { margin-top: 24px; }
.type-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 10px; }
.type-card { border: 1px solid #e4e7ed; border-radius: 8px; padding: 12px; cursor: pointer; transition: all 0.2s; text-align: center; }
.type-card:hover { border-color: #409eff; background: #f0f7ff; }
.type-card.active { border-color: #409eff; background: #ecf5ff; box-shadow: 0 0 0 1px #409eff; position: relative; }
.type-check { position: absolute; top: 6px; right: 6px; }
.selected-count { font-size: 12px; color: #409eff; font-weight: normal; margin-left: 8px; }
.type-tip { display: flex; align-items: center; gap: 4px; font-size: 12px; color: #909399; margin-top: 10px; }
.type-card { position: relative; }
.type-icon { font-size: 20px; }
.type-name { font-size: 13px; font-weight: 500; margin-top: 6px; color: #333; }
.type-name-en { font-size: 11px; color: #999; margin-top: 2px; }
.relate-section { margin-top: 20px; padding: 16px; background: #fafafa; border-radius: 8px; }
.relate-label { font-size: 12px; color: #606266; margin-bottom: 6px; display: block; }
.file-section { margin-top: 24px; }
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.progress-section { margin-top: 16px; }
.progress-text { font-size: 12px; color: #666; margin-top: 6px; }
.action-bar { margin-top: 20px; display: flex; align-items: center; gap: 12px; }
.tip-text { font-size: 12px; color: #f56c6c; }
.recent-section { margin-top: 32px; padding-top: 24px; border-top: 1px solid #eee; }
</style>
