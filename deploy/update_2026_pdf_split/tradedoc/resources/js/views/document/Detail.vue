<template>
  <div class="detail-page" v-loading="loading">
    <!-- 顶部操作栏 -->
    <div class="detail-header">
      <div class="header-left">
        <el-button @click="$router.push('/documents')" size="small"><el-icon><ArrowLeft /></el-icon> 返回列表</el-button>
        <el-tag v-if="doc" size="small" :type="getTagType(doc.document_type?.color)">{{ doc.document_type?.name }}</el-tag>
        <span class="doc-no">{{ doc?.doc_no }}</span>
        <el-tag :type="statusType(doc?.status)" size="small">{{ statusMap[doc?.status] }}</el-tag>
      </div>
      <div class="header-actions" v-if="doc">
        <el-button size="small" @click="handlePreview"><el-icon><View /></el-icon> 预览</el-button>
        <el-button size="small" @click="handleDownload"><el-icon><Download /></el-icon> 下载原件</el-button>
        <el-button size="small" @click="exportExcel"><el-icon><Document /></el-icon> 导出Excel</el-button>
        <el-button v-if="isPdf && !doc.is_split_container && !doc.parent_document_id" size="small" type="warning" @click="openSplitDialog" :loading="splitAnalyzing">
          <el-icon><Scissor /></el-icon> 智能拆分
        </el-button>
        <el-dropdown trigger="click" @command="handleStatusChange" v-if="availableStatuses.length > 0">
          <el-button size="small" type="primary"><el-icon><Switch /></el-icon> 状态变更 <el-icon><ArrowDown /></el-icon></el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item v-for="s in availableStatuses" :key="s.value" :command="s.value">
                {{ s.label }}
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        <el-button size="small" type="danger" @click="handleDelete"><el-icon><Delete /></el-icon> 删除</el-button>
      </div>
    </div>

    <div class="detail-body" v-if="doc">
      <el-row :gutter="16">
        <!-- 左侧：文件预览 -->
        <el-col :span="12">
          <el-card shadow="never">
            <template #header>
              <div class="card-header">
                <span>文件预览</span>
                <el-button size="small" @click="fullscreenPreview = true"><el-icon><FullScreen /></el-icon> 全屏预览</el-button>
              </div>
            </template>
            <div class="preview-area" @dblclick="fullscreenPreview = true" title="双击放大预览">
              <div v-if="isImage" class="preview-img">
                <img :src="previewSrc" alt="预览" />
              </div>
              <iframe v-else-if="isPdf" :src="previewSrc" class="preview-pdf"></iframe>
              <div v-else class="preview-placeholder">
                <el-icon :size="48"><Document /></el-icon>
                <p>{{ doc.original_filename }}</p>
                <p class="sub">{{ doc.file_ext?.toUpperCase() }} · {{ formatSize(doc.file_size) }}</p>
                <el-button size="small" type="primary" @click="handleDownload" style="margin-top:12px;">下载查看</el-button>
              </div>
            </div>
          </el-card>

          <!-- 全屏预览弹窗 -->
          <el-dialog v-model="fullscreenPreview" title="文件预览" fullscreen append-to-body>
            <div class="fullscreen-preview">
              <div v-if="isImage" class="fullscreen-img">
                <img :src="previewSrc" alt="预览" />
              </div>
              <iframe v-else-if="isPdf" :src="previewSrc" class="fullscreen-pdf"></iframe>
            </div>
          </el-dialog>
        </el-col>

        <!-- 右侧 -->
        <el-col :span="12">
          <!-- 提取字段 -->
          <el-card shadow="never">
            <template #header>
              <div class="card-header">
                <div style="display:flex;align-items:center;gap:8px;">
                  <span>提取字段</span>
                  <el-tag v-if="doc.ocr_confidence" size="small" :type="doc.ocr_confidence >= 90 ? 'success' : 'warning'">
                    置信度 {{ doc.ocr_confidence }}%
                  </el-tag>
                </div>
                <div style="display:flex;gap:6px;">
                  <el-button size="small" @click="reOcr" :loading="ocrRunning"><el-icon><RefreshRight /></el-icon> 重新识别</el-button>
                  <el-button size="small" type="primary" @click="showAddField = true"><el-icon><Plus /></el-icon> 添加字段</el-button>
                </div>
              </div>
            </template>

            <!-- 字段列表 — 直接编辑模式 -->
            <div class="field-list">
              <div v-for="field in doc.fields" :key="field.id" class="field-row">
                <div class="field-label">
                  <span class="field-name">{{ field.template?.field_name || field.field_key }}</span>
                  <span class="field-conf" v-if="field.confidence" :style="{ color: field.confidence >= 80 ? '#67c23a' : '#e6a23c' }">
                    {{ field.confidence }}%
                  </span>
                </div>
                <div class="field-input-wrap">
                  <el-input
                    v-model="fieldValues[field.id]"
                    size="small"
                    :placeholder="field.template?.field_name || '输入值'"
                    :class="{ 'changed': fieldValues[field.id] !== (field.field_value || '') }"
                    @blur="autoSaveField(field)"
                  >
                    <template #suffix>
                      <el-tag v-if="field.is_confirmed" type="success" size="small" class="field-status-tag">已确认</el-tag>
                      <el-tag v-else-if="field.extract_method === 'manual'" type="info" size="small" class="field-status-tag">手动</el-tag>
                      <el-tag v-else type="warning" size="small" class="field-status-tag">自动</el-tag>
                    </template>
                  </el-input>
                </div>
                <el-tooltip content="从缓存填值" placement="top" v-if="!fieldValues[field.id]">
                  <el-button size="small" :icon="Search" circle @click="ocrSingleField(field)" :loading="field._ocrLoading" />
                </el-tooltip>
                <el-tooltip content="删除字段" placement="top">
                  <el-button size="small" :icon="Delete" circle type="danger" plain @click="deleteField(field)" />
                </el-tooltip>
              </div>
            </div>

            <!-- 空状态 -->
            <el-empty v-if="!doc.fields?.length" description="暂无提取字段" :image-size="48">
              <el-button size="small" type="primary" @click="showAddField = true">手动添加字段</el-button>
            </el-empty>

            <!-- 底部操作 -->
            <div class="field-actions" v-if="hasChangedFields">
              <el-button type="primary" size="small" @click="saveAllFields" :loading="fieldSaving">
                <el-icon><Check /></el-icon> 保存所有修改
              </el-button>
              <el-button size="small" @click="resetFields">重置</el-button>
              <span class="changed-tip">{{ changedCount }} 个字段已修改</span>
            </div>
            <div class="field-tip">直接编辑字段值，离开输入框自动保存；留空表示未识别</div>
          </el-card>

          <!-- 添加字段弹窗 -->
          <el-dialog v-model="showAddField" title="添加字段" width="500px">
            <el-form label-width="80px" size="small">
              <el-form-item label="来源">
                <el-radio-group v-model="addFieldMode" size="small">
                  <el-radio-button label="template">从模板选择</el-radio-button>
                  <el-radio-button label="manual">手动输入</el-radio-button>
                </el-radio-group>
              </el-form-item>

              <!-- 模板选择模式 -->
              <el-form-item label="选择字段" v-if="addFieldMode === 'template'">
                <el-select v-model="newFieldKey" placeholder="从模板选择..." filterable clearable style="width:100%">
                  <el-option
                    v-for="tmpl in availableTemplates"
                    :key="tmpl.field_key"
                    :label="`${tmpl.field_name} (${tmpl.field_key})`"
                    :value="tmpl.field_key"
                  />
                </el-select>
              </el-form-item>

              <!-- 手动输入模式 -->
              <template v-if="addFieldMode === 'manual'">
                <el-form-item label="字段标识">
                  <el-input v-model="newFieldKey" placeholder="如: invoice_no, buyer_name" />
                  <div class="form-tip">英文标识，用于系统内部关联，如 declaration_no</div>
                </el-form-item>
                <el-form-item label="字段名称">
                  <el-input v-model="newFieldName" placeholder="如: 发票号, 买方名称" />
                  <div class="form-tip">中文显示名称</div>
                </el-form-item>
              </template>

              <el-form-item label="字段值">
                <el-input v-model="newFieldValue" placeholder="输入值，可留空" />
              </el-form-item>
            </el-form>
            <template #footer>
              <el-button @click="showAddField = false">取消</el-button>
              <el-button type="primary" @click="addField" :loading="fieldSaving" :disabled="!newFieldKey">确定添加</el-button>
            </template>
          </el-dialog>

          <!-- 基本信息 -->
          <el-card shadow="never" class="mt-16">
            <template #header><span>基本信息</span></template>
            <el-descriptions :column="2" size="small" border>
              <el-descriptions-item label="文件编号">{{ doc.doc_no }}</el-descriptions-item>
              <el-descriptions-item label="文件类型">{{ doc.document_type?.name }}</el-descriptions-item>
              <el-descriptions-item label="关联订单">{{ doc.order?.order_no || '—' }}</el-descriptions-item>
              <el-descriptions-item label="客户">{{ doc.customer?.company_name || '—' }}</el-descriptions-item>
              <el-descriptions-item label="上传人">{{ doc.uploader?.real_name }}</el-descriptions-item>
              <el-descriptions-item label="上传时间">{{ formatDate(doc.created_at) }}</el-descriptions-item>
              <el-descriptions-item label="文件大小">{{ formatSize(doc.file_size) }}</el-descriptions-item>
              <el-descriptions-item label="版本">v{{ doc.version }}</el-descriptions-item>
              <el-descriptions-item label="核对人">{{ doc.reviewer?.real_name || '—' }}</el-descriptions-item>
              <el-descriptions-item label="审批人">{{ doc.approver?.real_name || '—' }}</el-descriptions-item>
            </el-descriptions>
          </el-card>

          <!-- 父文档信息（如果当前是子文档）-->
          <el-card shadow="never" class="mt-16" v-if="doc.parent_document_id">
            <template #header>
              <span>所属父文档（拆分自）</span>
            </template>
            <div class="parent-info">
              <el-icon><Files /></el-icon>
              <span>该文档由父文档拆分而来</span>
              <span class="page-range" v-if="doc.split_page_range">页码 {{ doc.split_page_range }}</span>
              <el-button size="small" type="primary" plain @click="$router.push('/documents/' + doc.parent_document_id)">查看父文档</el-button>
            </div>
          </el-card>

          <!-- 子文档列表（如果当前是父文档）-->
          <el-card shadow="never" class="mt-16" v-if="doc.is_split_container">
            <template #header>
              <span>拆分子文档</span>
              <el-tag size="small" type="info" style="margin-left:8px;">已归档容器</el-tag>
            </template>
            <div v-loading="loadingChildren">
              <el-empty v-if="!children.length" description="无子文档" :image-size="48" />
              <div v-else class="children-list">
                <div v-for="child in children" :key="child.id" class="child-row" @click="$router.push('/documents/' + child.id)">
                  <el-tag size="small" :type="getTagType(child.document_type?.color)">{{ child.document_type?.name }}</el-tag>
                  <span class="child-no">{{ child.doc_no }}</span>
                  <span class="child-range">页 {{ child.split_page_range }}</span>
                  <el-tag size="small" :type="statusType(child.status)">{{ statusMap[child.status] }}</el-tag>
                  <el-icon><ArrowRight /></el-icon>
                </div>
              </div>
            </div>
          </el-card>

          <!-- 版本历史 -->
          <el-card shadow="never" class="mt-16" v-if="doc.versions?.length">
            <template #header><span>版本历史</span></template>
            <el-timeline>
              <el-timeline-item
                v-for="v in doc.versions"
                :key="v.id"
                :timestamp="formatDate(v.created_at)"
                placement="top"
              >
                v{{ v.version }} — {{ v.change_summary || '上传' }} · {{ formatSize(v.file_size) }}
              </el-timeline-item>
            </el-timeline>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 智能拆分对话框 -->
    <el-dialog v-model="splitDialogVisible" title="智能拆分预览" width="720px" :close-on-click-modal="false">
      <div v-if="splitAnalyzing" class="split-loading">
        <el-icon class="is-loading" :size="32"><Loading /></el-icon>
        <p>正在分析 PDF 内容...</p>
      </div>
      <div v-else>
        <el-alert v-if="splitAnalysis?.is_scanned" type="warning" :closable="false" show-icon>
          检测到这是扫描件，无法自动识别页内容。建议先用 OCR 重新识别后再拆分。
        </el-alert>
        <el-alert v-else-if="!splitAnalysis?.suggest_split" type="info" :closable="false" show-icon>
          该 PDF 仅包含一种单证类型，无需拆分。
        </el-alert>

        <div v-else>
          <p class="split-summary">
            共 <strong>{{ splitAnalysis.total_pages }}</strong> 页，识别出 <strong>{{ splitSegments.length }}</strong> 段，可拆分为 {{ validSegmentCount }} 个独立子文档（unknown 段不会被拆分）。
          </p>
          <el-table :data="splitSegments" size="small" border>
            <el-table-column label="页范围" prop="page_range" width="80" align="center" />
            <el-table-column label="自动识别类型" width="220">
              <template #default="{ row, $index }">
                <el-select v-model="splitSegments[$index].type_code" size="small" style="width:100%" :placeholder="row.type_code === 'unknown' ? '未识别，请选择类型' : ''">
                  <el-option label="（不拆分此段）" value="unknown" />
                  <el-option v-for="t in docTypes" :key="t.code" :label="t.name + ' (' + t.code + ')'" :value="t.code" />
                </el-select>
              </template>
            </el-table-column>
            <el-table-column label="置信度" width="100" align="center">
              <template #default="{ row }">
                <el-tag v-if="row.confidence >= 80" type="success" size="small">{{ row.confidence }}%</el-tag>
                <el-tag v-else-if="row.confidence > 0" type="warning" size="small">{{ row.confidence }}%</el-tag>
                <el-tag v-else type="info" size="small">未知</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="页数" prop="page_count" width="60" align="center" />
          </el-table>
          <div class="split-tip">
            <el-icon><InfoFilled /></el-icon>
            拆分后原 PDF 会标记为「已归档容器」，子文档独立 OCR 提取字段。操作不可撤销，请谨慎确认。
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="splitDialogVisible = false">取消</el-button>
        <el-button
          type="primary"
          :loading="splitExecuting"
          :disabled="!splitAnalysis?.suggest_split || validSegmentCount < 1"
          @click="confirmSplit"
        >确认拆分</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Search, Delete, Scissor, Loading, Files, ArrowRight, InfoFilled } from '@element-plus/icons-vue';
import { documentApi } from '@/api/document';
import { useAuthStore } from '@/stores/auth';
import http from '@/api/http';

const route = useRoute();
const router = useRouter();
const auth = useAuthStore();
const loading = ref(true);
const doc = ref(null);

// 预览
const fullscreenPreview = ref(false);

// OCR 重新识别
const ocrRunning = ref(false);

// PDF 智能拆分
const splitDialogVisible = ref(false);
const splitAnalyzing = ref(false);
const splitExecuting = ref(false);
const splitAnalysis = ref(null);
const splitSegments = ref([]);
const docTypes = ref([]);
const children = ref([]);
const loadingChildren = ref(false);

const validSegmentCount = computed(() =>
  splitSegments.value.filter(s => s.type_code && s.type_code !== 'unknown').length
);

// 字段编辑
const fieldValues = ref({});    // { fieldId: value }
const fieldOriginal = ref({}); // 原始值，用于对比变化
const fieldSaving = ref(false);
const showAddField = ref(false);
const addFieldMode = ref('template');
const newFieldKey = ref('');
const newFieldName = ref('');
const newFieldValue = ref('');
const availableTemplates = ref([]);

const statusMap = {
    draft: '待处理', ocr_processing: '识别中', pending_review: '待核对',
    pending_approval: '待审批', approved: '已审批', archived: '已归档', voided: '已作废',
};

const statusTransitions = {
    draft: [{ value: 'ocr_processing', label: '提交OCR识别' }],
    ocr_processing: [{ value: 'pending_review', label: '转为待核对' }],
    pending_review: [
        { value: 'pending_approval', label: '提交审核' },
        { value: 'ocr_processing', label: '重新OCR' },
    ],
    pending_approval: [
        { value: 'archived', label: '审核通过并归档' },
        { value: 'pending_review', label: '驳回重新核对' },
    ],
    archived: [],
};

const availableStatuses = computed(() => {
    return statusTransitions[doc.value?.status] || [];
});

const isImage = computed(() => ['jpg', 'jpeg', 'png', 'gif'].includes(doc.value?.file_ext?.toLowerCase()));
const isPdf = computed(() => doc.value?.file_ext?.toLowerCase() === 'pdf');
const previewSrc = computed(() => {
    if (!doc.value) return '';
    return `/api/v1/documents/${doc.value.id}/preview`;
});

function statusType(s) {
    return { draft: 'info', ocr_processing: 'warning', pending_review: 'warning', pending_approval: '', archived: 'success', voided: 'danger' }[s] || 'info';
}
function getTagType(c) {
    return { blue: '', green: 'success', amber: 'warning', coral: 'danger', gray: 'info' }[c] || 'info';
}
function formatSize(b) {
    if (!b) return '0 B';
    const k = 1024, s = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(b) / Math.log(k));
    return (b / Math.pow(k, i)).toFixed(1) + ' ' + s[i];
}
function formatDate(str) {
    if (!str) return '';
    return new Date(str).toLocaleString('zh-CN');
}

async function loadDetail() {
    loading.value = true;
    try {
        const res = await documentApi.detail(route.params.id);
        doc.value = res.data;
        initFieldValues();
        loadAvailableTemplates();
        // 加载所需附属数据
        if (doc.value?.is_split_container) {
            loadChildren();
        }
        if (docTypes.value.length === 0) {
            loadDocTypes();
        }
    } finally {
        loading.value = false;
    }
}

async function loadDocTypes() {
    try {
        const res = await documentApi.types();
        docTypes.value = res.data || [];
    } catch (e) { /* ignore */ }
}

async function loadChildren() {
    if (!doc.value?.id) return;
    loadingChildren.value = true;
    try {
        // 借用列表接口拉所有子文档
        const res = await documentApi.list({ parent_document_id: doc.value.id, per_page: 100 });
        children.value = (res.data?.data || res.data || []).filter(d => d.parent_document_id === doc.value.id);
    } catch (e) {
        children.value = [];
    } finally {
        loadingChildren.value = false;
    }
}

// 打开智能拆分对话框
async function openSplitDialog() {
    if (docTypes.value.length === 0) {
        await loadDocTypes();
    }
    splitDialogVisible.value = true;
    splitAnalyzing.value = true;
    splitAnalysis.value = null;
    splitSegments.value = [];
    try {
        const res = await documentApi.analyzeSplit(doc.value.id);
        splitAnalysis.value = res.data;
        // 复制 segments 让用户可调整 type_code
        splitSegments.value = (res.data?.segments || []).map(s => ({ ...s }));
    } catch (e) {
        ElMessage.error('分析失败: ' + (e?.response?.data?.error || e.message || '未知错误'));
        splitDialogVisible.value = false;
    } finally {
        splitAnalyzing.value = false;
    }
}

// 确认执行拆分
async function confirmSplit() {
    const valid = splitSegments.value.filter(s => s.type_code && s.type_code !== 'unknown');
    if (valid.length === 0) {
        ElMessage.warning('请至少为一段指定类型');
        return;
    }
    try {
        await ElMessageBox.confirm(
            `将把当前 PDF 拆分为 ${valid.length} 个独立子文档，原 PDF 会归档保留。是否继续？`,
            '确认拆分',
            { confirmButtonText: '确认', cancelButtonText: '取消', type: 'warning' }
        );
    } catch (e) {
        return; // 用户取消
    }

    splitExecuting.value = true;
    try {
        const payload = valid.map(s => ({
            type_code: s.type_code,
            page_start: s.page_start,
            page_end: s.page_end,
        }));
        const res = await documentApi.executeSplit(doc.value.id, payload);
        const count = res.data?.children?.length || 0;
        ElMessage.success(`拆分完成，创建了 ${count} 个子文档`);
        splitDialogVisible.value = false;
        // 重新加载详情，此时父文档已是容器
        await loadDetail();
    } catch (e) {
        const errors = e?.response?.data?.errors || [e?.response?.data?.message || e.message];
        ElMessage.error('拆分失败：' + (Array.isArray(errors) ? errors.join('；') : errors));
    } finally {
        splitExecuting.value = false;
    }
}

function handlePreview() {
    window.open(previewSrc.value, '_blank');
}

function exportExcel() {
    const token = localStorage.getItem('token');
    window.open(`/api/v1/documents/${doc.value.id}/export?token=${token}`, '_blank');
}

async function handleDownload() {
    try {
        const res = await documentApi.download(doc.value.id);
        const url = URL.createObjectURL(new Blob([res]));
        const a = document.createElement('a');
        a.href = url;
        a.download = doc.value.original_filename;
        a.click();
        URL.revokeObjectURL(url);
    } catch {
        ElMessage.error('下载失败');
    }
}

async function handleDelete() {
    try {
        await ElMessageBox.confirm(
            `确定要删除文件 ${doc.value.doc_no} 吗？删除后可在回收站恢复。`,
            '确认删除',
            { type: 'warning', confirmButtonText: '确定删除', cancelButtonText: '取消' }
        );
        await documentApi.delete(doc.value.id);
        ElMessage.success('文件已删除');
        router.push('/documents');
    } catch (e) {
        if (e !== 'cancel') ElMessage.error('删除失败');
    }
}

async function handleStatusChange(status) {
    const label = availableStatuses.value.find(s => s.value === status)?.label || status;
    try {
        await ElMessageBox.confirm(`确定要将文件状态变更为「${label}」吗？`, '状态变更', {
            confirmButtonText: '确定', cancelButtonText: '取消',
        });
        await documentApi.changeStatus(doc.value.id, status);
        ElMessage.success('状态已更新');
        loadDetail();
    } catch (e) {
        if (e !== 'cancel') ElMessage.error('状态变更失败');
    }
}

// 计算属性
const hasChangedFields = computed(() => changedCount.value > 0);
const changedCount = computed(() => {
    let count = 0;
    for (const [id, val] of Object.entries(fieldValues.value)) {
        if (val !== (fieldOriginal.value[id] || '')) count++;
    }
    return count;
});

// 初始化字段编辑值
function initFieldValues() {
    const vals = {};
    const orig = {};
    for (const f of (doc.value?.fields || [])) {
        vals[f.id] = f.field_value || '';
        orig[f.id] = f.field_value || '';
    }
    fieldValues.value = vals;
    fieldOriginal.value = orig;
}

// 自动保存（离开输入框时）
async function autoSaveField(field) {
    const newVal = fieldValues.value[field.id];
    const oldVal = fieldOriginal.value[field.id] || '';
    if (newVal === oldVal) return; // 没变化不保存

    try {
        await documentApi.updateField(field.id, newVal);
        fieldOriginal.value[field.id] = newVal;
        // 更新本地数据
        const f = doc.value.fields.find(x => x.id === field.id);
        if (f) { f.field_value = newVal; f.is_confirmed = true; }
    } catch {
        ElMessage.error('保存失败');
    }
}

// 保存所有修改
async function saveAllFields() {
    fieldSaving.value = true;
    let saved = 0;
    try {
        for (const [id, val] of Object.entries(fieldValues.value)) {
            if (val !== (fieldOriginal.value[id] || '')) {
                await documentApi.updateField(parseInt(id), val);
                fieldOriginal.value[id] = val;
                saved++;
            }
        }
        ElMessage.success(`已保存 ${saved} 个字段`);
        loadDetail();
    } catch {
        ElMessage.error('部分保存失败');
    } finally {
        fieldSaving.value = false;
    }
}

function resetFields() {
    initFieldValues();
}

// 添加新字段
async function addField() {
    if (!newFieldKey.value) return;
    fieldSaving.value = true;
    try {
        await http.post('/documents/add-field', {
            document_id: doc.value.id,
            field_key: newFieldKey.value,
            field_name: newFieldName.value || '',
            field_value: newFieldValue.value || '',
        });
        ElMessage.success('字段已添加');
        showAddField.value = false;
        newFieldKey.value = '';
        newFieldName.value = '';
        newFieldValue.value = '';
        addFieldMode.value = 'template';
        loadDetail();
    } catch {
        ElMessage.error('添加失败');
    } finally {
        fieldSaving.value = false;
    }
}

// 加载可添加的字段模板（排除已有的）
async function loadAvailableTemplates() {
    if (!doc.value?.document_type_id) return;
    try {
        const res = await http.get(`/admin/field-templates/${doc.value.document_type_id}`);
        const existingKeys = new Set((doc.value.fields || []).map(f => f.field_key));
        availableTemplates.value = (res.data || []).filter(t => !existingKeys.has(t.field_key));
    } catch {}
}

// 重新识别全部字段
async function reOcr() {
    try {
        await ElMessageBox.confirm(
            '将对该文件重新进行智能识别，已有的自动提取字段会被更新（手动确认的不会覆盖）。继续？',
            '重新识别',
            { confirmButtonText: '开始识别', cancelButtonText: '取消', type: 'info' }
        );
    } catch { return; }

    ocrRunning.value = true;
    try {
        await http.post('/documents/re-ocr', { document_id: doc.value.id });
        ElMessage.success('识别完成，字段已更新');
        loadDetail();
    } catch {
        ElMessage.error('识别失败，请检查 Python 服务是否运行');
    } finally {
        ocrRunning.value = false;
    }
}

// 单独填充一个字段（从缓存取值，不重新调 OCR）
async function ocrSingleField(field) {
    field._ocrLoading = true;
    try {
        const cache = await http.get(`/documents/${doc.value.id}/ocr-cache`);

        if (!cache.cached) {
            ElMessage.warning('没有识别缓存，请先点击「重新识别」');
            return;
        }

        const cached = cache.data[field.field_key];
        if (cached && cached.value) {
            fieldValues.value[field.id] = cached.value;
            await documentApi.updateField(field.id, cached.value);
            ElMessage.success(`已填充: ${cached.value}`);
            loadDetail();
        } else {
            // 缓存有这个 key 但值为空，说明 OCR 没识别到
            ElMessage.info('未识别到此字段内容，请手动输入或重新识别');
        }
    } catch {
        ElMessage.error('获取缓存失败，请确认 Python 服务运行中');
    } finally {
        field._ocrLoading = false;
    }
}

// 删除字段
async function deleteField(field) {
    const name = field.template?.field_name || field.field_key;
    try {
        await ElMessageBox.confirm(`确定删除字段「${name}」吗？`, '删除字段', {
            confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning',
        });
        await http.delete(`/documents/fields/${field.id}`);
        ElMessage.success('字段已删除');
        loadDetail();
    } catch (e) {
        if (e !== 'cancel') ElMessage.error('删除失败');
    }
}

onMounted(loadDetail);

// SPA 路由切换时（点子/父文档跳转）重新加载详情
watch(() => route.params.id, (newId, oldId) => {
    if (newId && newId !== oldId) {
        loadDetail();
    }
});
</script>

<style scoped>
.detail-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; flex-wrap: wrap; gap: 8px; }
.header-left { display: flex; align-items: center; gap: 10px; }
.header-actions { display: flex; gap: 8px; }
.doc-no { font-size: 16px; font-weight: 600; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.preview-area { min-height: 300px; display: flex; align-items: center; justify-content: center; background: #fafafa; border-radius: 8px; overflow: hidden; cursor: pointer; }
.preview-area:hover { background: #f0f0f0; }
.preview-img img { max-width: 100%; max-height: 500px; }
.preview-pdf { width: 100%; height: 500px; border: none; }
.fullscreen-preview { width: 100%; height: calc(100vh - 100px); }
.fullscreen-img { width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; overflow: auto; }
.fullscreen-img img { max-width: 100%; max-height: 100%; object-fit: contain; }
.fullscreen-pdf { width: 100%; height: 100%; border: none; }
.preview-placeholder { text-align: center; color: #999; padding: 40px; }
.preview-placeholder .sub { font-size: 12px; color: #c0c4cc; }
.field-list { display: flex; flex-direction: column; gap: 8px; }
.field-row { display: flex; align-items: center; gap: 8px; }
.field-label { width: 90px; flex-shrink: 0; }
.field-name { font-size: 12px; color: #606266; }
.field-conf { font-size: 10px; margin-left: 4px; }
.field-input-wrap { flex: 1; }
.field-input-wrap :deep(.changed .el-input__wrapper) { box-shadow: 0 0 0 1px #e6a23c inset; }
.field-status-tag { transform: scale(0.85); }
.field-actions { display: flex; align-items: center; gap: 8px; margin-top: 12px; padding-top: 12px; border-top: 1px solid #eee; }
.changed-tip { font-size: 11px; color: #e6a23c; }
.field-tip { font-size: 11px; color: #c0c4cc; margin-top: 8px; }
.form-tip { font-size: 11px; color: #c0c4cc; margin-top: 2px; }
.mt-16 { margin-top: 16px; }

/* 智能拆分相关 */
.split-loading { text-align: center; padding: 40px; color: #909399; }
.split-loading p { margin-top: 12px; }
.split-summary { font-size: 13px; color: #606266; margin: 0 0 12px; }
.split-tip { display: flex; align-items: center; gap: 6px; margin-top: 12px; font-size: 12px; color: #909399; padding: 8px 10px; background: #f4f4f5; border-radius: 4px; }
.parent-info { display: flex; align-items: center; gap: 10px; font-size: 13px; color: #606266; }
.parent-info .page-range { padding: 2px 10px; background: #f0f7ff; color: #409eff; border-radius: 4px; font-size: 12px; }
.children-list { display: flex; flex-direction: column; gap: 8px; }
.child-row { display: flex; align-items: center; gap: 10px; padding: 10px 12px; background: #fafafa; border-radius: 6px; cursor: pointer; transition: background .2s; }
.child-row:hover { background: #ecf5ff; }
.child-no { font-weight: 500; color: #303133; font-size: 13px; }
.child-range { padding: 2px 8px; background: #fff; border: 1px solid #e4e7ed; border-radius: 4px; font-size: 11px; color: #606266; }
.child-row .el-icon:last-child { margin-left: auto; color: #c0c4cc; }
</style>
