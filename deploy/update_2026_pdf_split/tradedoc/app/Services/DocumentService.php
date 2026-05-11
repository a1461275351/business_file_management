<?php

declare(strict_types=1);

namespace App\Services;

use App\Models\Document;
use App\Models\DocumentField;
use App\Models\DocumentType;
use App\Models\DocumentVersion;
use App\Models\OcrTask;
use Illuminate\Http\UploadedFile;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Storage;

class DocumentService
{
    /**
     * 上传并创建文件记录
     */
    public function upload(UploadedFile $file, int $typeId, int $userId, ?int $orderId = null, ?int $customerId = null): Document
    {
        return DB::transaction(function () use ($file, $typeId, $userId, $orderId, $customerId) {
            $docType = DocumentType::findOrFail($typeId);

            // 生成存储路径: 年/月/文件类型编码/
            $storagePath = sprintf(
                'documents/%s/%s/%s',
                now()->format('Y'),
                now()->format('m'),
                $docType->code
            );

            // 生成文件名
            $docNo = Document::generateDocNo($docType->code);
            $ext = $file->getClientOriginalExtension();
            $filename = $docNo . '_v1.' . $ext;

            // 存储文件
            $fullPath = $file->storeAs($storagePath, $filename, 'local');

            // 计算文件 hash
            $fileHash = hash_file('sha256', $file->getRealPath());

            // 创建文件记录
            $document = Document::create([
                'doc_no' => $docNo,
                'document_type_id' => $typeId,
                'order_id' => $orderId,
                'customer_id' => $customerId,
                'title' => $file->getClientOriginalName(),
                'original_filename' => $file->getClientOriginalName(),
                'storage_path' => $fullPath,
                'file_size' => $file->getSize(),
                'file_ext' => $ext,
                'mime_type' => $file->getMimeType(),
                'file_hash' => $fileHash,
                'language' => 'zh',
                'version' => 1,
                'status' => 'draft',
                'uploaded_by' => $userId,
            ]);

            // 创建版本记录
            DocumentVersion::create([
                'document_id' => $document->id,
                'version' => 1,
                'storage_path' => $fullPath,
                'file_size' => $file->getSize(),
                'file_hash' => $fileHash,
                'change_summary' => '初始上传',
                'created_by' => $userId,
                'created_at' => now(),
            ]);

            return $document;
        });
    }

    /**
     * 批量上传
     */
    public function batchUpload(array $files, int $typeId, int $userId, ?int $orderId = null): array
    {
        $results = [];
        foreach ($files as $file) {
            $results[] = $this->upload($file, $typeId, $userId, $orderId);
        }
        return $results;
    }

    /**
     * 分析 PDF 是否需要拆分（调 Python）
     */
    public function analyzeSplit(Document $document): array
    {
        // 非 PDF 直接跳过
        if (strtolower($document->file_ext ?? '') !== 'pdf') {
            return ['success' => true, 'data' => [
                'suggest_split' => false,
                'total_pages' => 1,
                'is_scanned' => false,
                'segments' => [],
                'pages' => [],
            ]];
        }

        $absPath = Storage::disk('local')->path($document->storage_path);
        $splitter = app(SplitterService::class);
        return $splitter->analyze($absPath);
    }

    /**
     * 执行拆分：按 segments 把父文档拆成 N 个子文档
     *
     * @param Document $parent 原始上传的文档（成为父文档）
     * @param array $segments [{type_code, page_start, page_end}, ...]
     * @param int $userId 操作人
     * @return array{success: bool, children: Document[], errors: array}
     */
    public function executeSplit(Document $parent, array $segments, int $userId): array
    {
        if (empty($segments)) {
            return ['success' => false, 'children' => [], 'errors' => ['未提供任何段']];
        }

        $sourceAbsPath = Storage::disk('local')->path($parent->storage_path);
        if (!file_exists($sourceAbsPath)) {
            return ['success' => false, 'children' => [], 'errors' => ['源文件不存在']];
        }

        // 1. 给每段预生成 doc_no 和子文件名
        //    用本地缓存避免循环内重复调 generateDocNo（数据库尚未插入新记录会拿到同一序号）
        $specsForPython = [];
        $childPlans = [];  // 暂存子文档计划，等 Python 拆分成功后再入库
        $seqByPrefix = []; // 缓存每个前缀的下一个可用序号
        foreach ($segments as $seg) {
            $typeCode = $seg['type_code'] ?? 'other';
            $typeId = $this->typeIdFromCode($typeCode);
            if (!$typeId) {
                continue; // 未知类型跳过（unknown 段不拆）
            }
            $docNo = $this->nextDocNo($typeCode, $seqByPrefix);
            $filename = $docNo . '_v1.pdf';

            $specsForPython[] = [
                'type_code' => $typeCode,
                'page_start' => (int) $seg['page_start'],
                'page_end' => (int) $seg['page_end'],
                'output_filename' => $filename,
            ];
            $childPlans[] = [
                'doc_no' => $docNo,
                'filename' => $filename,
                'type_id' => $typeId,
                'type_code' => $typeCode,
                'page_start' => (int) $seg['page_start'],
                'page_end' => (int) $seg['page_end'],
                'page_range' => $seg['page_start'] === $seg['page_end']
                    ? (string) $seg['page_start']
                    : ($seg['page_start'] . '-' . $seg['page_end']),
            ];
        }

        if (empty($specsForPython)) {
            return ['success' => false, 'children' => [], 'errors' => ['所有段都是未知类型，无可拆分']];
        }

        // 2. 子文件统一放父文档同目录下的 split/ 子目录
        $parentDir = dirname(Storage::disk('local')->path($parent->storage_path));
        $outputDir = $parentDir . DIRECTORY_SEPARATOR . 'split';

        // 3. 调 Python 拆分
        $splitter = app(SplitterService::class);
        $splitResp = $splitter->execute($sourceAbsPath, $outputDir, $specsForPython);

        if (empty($splitResp['success']) || empty($splitResp['results'])) {
            return [
                'success' => false,
                'children' => [],
                'errors' => $splitResp['errors'] ?? [$splitResp['error'] ?? '拆分失败'],
            ];
        }

        // 4. 拆分成功后写入子文档记录 + 标记父文档为容器
        return DB::transaction(function () use ($parent, $childPlans, $splitResp, $userId) {
            $children = [];

            // 把 Python 返回的 results 按文件名映射回 childPlans
            $resultsByFilename = [];
            foreach ($splitResp['results'] as $r) {
                $resultsByFilename[basename((string) $r['output_path'])] = $r;
            }

            foreach ($childPlans as $plan) {
                $r = $resultsByFilename[$plan['filename']] ?? null;
                if (!$r) {
                    continue; // 该段拆分失败
                }

                // 计算 storage_path（相对路径，相对 local disk）
                $relativePath = str_replace('\\', '/', $r['output_path']);
                $diskRoot = str_replace('\\', '/', Storage::disk('local')->path(''));
                $relativePath = ltrim(str_replace($diskRoot, '', $relativePath), '/');

                $child = Document::create([
                    'doc_no' => $plan['doc_no'],
                    'document_type_id' => $plan['type_id'],
                    'order_id' => $parent->order_id,
                    'customer_id' => $parent->customer_id,
                    'parent_document_id' => $parent->id,
                    'split_page_range' => $plan['page_range'],
                    'is_split_container' => false,
                    'title' => $parent->original_filename . ' [' . $plan['page_range'] . '页]',
                    'original_filename' => $plan['filename'],
                    'storage_path' => $relativePath,
                    'file_size' => $r['file_size'] ?? null,
                    'file_ext' => 'pdf',
                    'mime_type' => 'application/pdf',
                    'file_hash' => is_file($r['output_path']) ? hash_file('sha256', $r['output_path']) : null,
                    'language' => $parent->language ?? 'zh',
                    'version' => 1,
                    'status' => 'draft',
                    'uploaded_by' => $userId,
                ]);

                DocumentVersion::create([
                    'document_id' => $child->id,
                    'version' => 1,
                    'storage_path' => $relativePath,
                    'file_size' => $r['file_size'] ?? null,
                    'file_hash' => $child->file_hash,
                    'change_summary' => '从父文档拆分（页 ' . $plan['page_range'] . '）',
                    'created_by' => $userId,
                    'created_at' => now(),
                ]);

                // 自动提交 OCR
                $this->submitOcr($child);
                $children[] = $child;
            }

            // 标记父文档为容器，状态归档（仅作存档，不再做 OCR）
            $parent->update([
                'is_split_container' => true,
                'status' => 'archived',
                'archived_at' => now(),
            ]);

            return [
                'success' => count($children) > 0,
                'children' => $children,
                'errors' => $splitResp['errors'] ?? [],
            ];
        });
    }

    /**
     * 由 type_code 查 document_type_id
     */
    private function typeIdFromCode(string $code): ?int
    {
        if ($code === 'unknown' || $code === '') {
            return null;
        }
        $type = DocumentType::where('code', $code)->first();
        return $type?->id;
    }

    /**
     * 循环安全的 doc_no 生成：用 $seqCache 缓存每个前缀的下一个序号
     * 比直接调 Document::generateDocNo() 安全，因为不依赖"刚插入的记录已可见"
     */
    private function nextDocNo(string $typeCode, array &$seqCache): string
    {
        $prefix = match ($typeCode) {
            'customs_declaration' => 'D',
            'commercial_invoice' => 'INV',
            'packing_list' => 'PL',
            'bank_receipt' => 'BK',
            'bill_of_lading' => 'BL',
            'certificate_of_origin' => 'CO',
            'contract' => 'CT',
            'letter_of_credit' => 'LC',
            default => 'DOC',
        };
        $date = now()->format('ymd');

        if (!isset($seqCache[$prefix])) {
            // 首次：查数据库当天该前缀的最大序号（包含软删除避免冲突）
            $maxNo = Document::withTrashed()
                ->where('doc_no', 'like', $prefix . $date . '-%')
                ->orderByDesc('doc_no')
                ->value('doc_no');
            $seqCache[$prefix] = ($maxNo && preg_match('/-(\d+)$/', $maxNo, $m))
                ? (int) $m[1]
                : 0;
        }

        $seqCache[$prefix]++;
        return sprintf('%s%s-%04d', $prefix, $date, $seqCache[$prefix]);
    }

    /**
     * 提交 OCR 识别任务并触发 Python 处理
     */
    public function submitOcr(Document $document): OcrTask
    {
        $document->update(['status' => 'ocr_processing']);

        $task = OcrTask::create([
            'document_id' => $document->id,
            'task_type' => 'ocr',
            'status' => 'pending',
            'priority' => 5,
            'retry_count' => 0,
            'max_retries' => 3,
        ]);

        // 异步调用 Python OCR 服务（不阻塞上传响应）
        try {
            $ocrService = app(OcrService::class);
            $typeCode = $document->documentType?->code ?? '';
            $ocrService->processDocument($document->id, $typeCode);
        } catch (\Throwable $e) {
            // OCR 调用失败不影响上传，任务状态保持 pending，后续可重试
            \Illuminate\Support\Facades\Log::warning('OCR 自动触发失败', [
                'document_id' => $document->id,
                'error' => $e->getMessage(),
            ]);
        }

        return $task;
    }

    /**
     * 文件列表查询
     */
    public function list(array $filters, int $perPage = 20)
    {
        $query = Document::with(['documentType', 'uploader:id,real_name', 'order:id,order_no', 'customer:id,company_name']);

        if (!empty($filters['document_type_id'])) {
            $query->where('document_type_id', $filters['document_type_id']);
        }

        if (!empty($filters['status'])) {
            $query->where('status', $filters['status']);
        }

        if (!empty($filters['keyword'])) {
            $keyword = $filters['keyword'];
            $query->where(function ($q) use ($keyword) {
                $q->where('doc_no', 'like', "%{$keyword}%")
                  ->orWhere('title', 'like', "%{$keyword}%")
                  ->orWhere('original_filename', 'like', "%{$keyword}%");
            });
        }

        if (!empty($filters['date_from'])) {
            $query->where('created_at', '>=', $filters['date_from']);
        }

        if (!empty($filters['date_to'])) {
            $query->where('created_at', '<=', $filters['date_to'] . ' 23:59:59');
        }

        if (!empty($filters['customer_id'])) {
            $query->where('customer_id', $filters['customer_id']);
        }

        if (!empty($filters['order_id'])) {
            $query->where('order_id', $filters['order_id']);
        }

        if (!empty($filters['parent_document_id'])) {
            $query->where('parent_document_id', $filters['parent_document_id']);
        }

        return $query->orderByDesc('created_at')->paginate($perPage);
    }

    /**
     * 文件详情
     */
    public function detail(string|int $id): Document
    {
        return Document::with([
            'documentType',
            'uploader:id,real_name',
            'reviewer:id,real_name',
            'approver:id,real_name',
            'order:id,order_no',
            'customer:id,company_name',
            'fields.template',
            'versions',
        ])->findOrFail($id);
    }

    /**
     * 统计数据（仪表盘用）
     */
    public function statistics(): array
    {
        $totalThisMonth = Document::whereMonth('created_at', now()->month)
            ->whereYear('created_at', now()->year)->count();

        $pendingCount = Document::whereIn('status', ['draft', 'ocr_processing', 'pending_review', 'pending_approval'])->count();

        // 字段提取准确率（所有有置信度的字段的平均值）
        $ocrAccuracy = (float) (DB::table('document_fields')
            ->whereNotNull('confidence')
            ->where('confidence', '>', 0)
            ->avg('confidence') ?? 0);

        $totalFields = DB::table('document_fields')->count();

        // 类型分布：分两步查询避免 with+groupBy 冲突
        $distribution = DB::table('documents')
            ->join('document_types', 'documents.document_type_id', '=', 'document_types.id')
            ->whereMonth('documents.created_at', now()->month)
            ->whereYear('documents.created_at', now()->year)
            ->whereNull('documents.deleted_at')
            ->select('document_types.id', 'document_types.name', 'document_types.color', DB::raw('count(*) as count'))
            ->groupBy('document_types.id', 'document_types.name', 'document_types.color')
            ->get();

        return [
            'total_this_month' => $totalThisMonth,
            'pending_count' => $pendingCount,
            'ocr_accuracy' => round($ocrAccuracy, 1),
            'total_fields' => $totalFields,
            'type_distribution' => $distribution,
        ];
    }

    /**
     * 删除文件（软删除）
     */
    public function delete(string|int $id, int $userId): void
    {
        $document = Document::findOrFail($id);
        $document->update(['status' => 'voided']);
        $document->delete(); // 软删除
    }

    /**
     * 变更文件状态
     */
    public function changeStatus(string|int $id, string $status, int $userId): Document
    {
        $document = Document::findOrFail($id);

        $allowedTransitions = [
            'draft' => ['ocr_processing', 'voided'],
            'ocr_processing' => ['pending_review', 'voided'],
            'pending_review' => ['pending_approval', 'ocr_processing', 'voided'],
            'pending_approval' => ['archived', 'pending_review', 'voided'],
            'archived' => ['voided'],
            'voided' => [],
        ];

        $allowed = $allowedTransitions[$document->status] ?? [];
        if (!in_array($status, $allowed)) {
            throw new \InvalidArgumentException(
                sprintf('不允许从 [%s] 变更到 [%s]', $document->status, $status)
            );
        }

        $updateData = ['status' => $status];

        if ($status === 'archived') {
            $updateData['approved_by'] = $userId;
            $updateData['approved_at'] = now();
            $updateData['archived_at'] = now();
        }

        $document->update($updateData);

        return $document->fresh();
    }

    /**
     * 获取文件下载路径
     */
    public function getFilePath(string|int $id): array
    {
        $document = Document::findOrFail($id);
        $fullPath = Storage::disk('local')->path($document->storage_path);

        return [
            'path' => $fullPath,
            'filename' => $document->original_filename,
            'mime_type' => $document->mime_type,
        ];
    }

    /**
     * 更新文件字段值
     */
    public function updateField(int $fieldId, string $value, int $userId): DocumentField
    {
        $field = DocumentField::findOrFail($fieldId);
        $field->update([
            'field_value' => $value,
            'is_confirmed' => true,
            'confirmed_by' => $userId,
            'confirmed_at' => now(),
            'extract_method' => 'manual',
        ]);

        return $field->fresh();
    }

    /**
     * 手动添加字段
     */
    public function addField(int $documentId, string $fieldKey, string $value, int $userId, string $fieldName = ''): DocumentField
    {
        $document = Document::findOrFail($documentId);

        // 查找已有的字段模板
        $template = \App\Models\FieldTemplate::where('document_type_id', $document->document_type_id)
            ->where('field_key', $fieldKey)
            ->first();

        // 手动输入的字段如果模板不存在，自动创建模板
        if (!$template && $fieldName) {
            $maxSort = \App\Models\FieldTemplate::where('document_type_id', $document->document_type_id)
                ->max('sort_order') ?? 0;

            $template = \App\Models\FieldTemplate::create([
                'document_type_id' => $document->document_type_id,
                'field_key' => $fieldKey,
                'field_name' => $fieldName,
                'field_name_en' => $fieldKey,
                'field_type' => 'string',
                'is_required' => false,
                'is_auto_extract' => false,
                'sort_order' => $maxSort + 1,
                'status' => 1,
            ]);
        }

        // 如果没填值，从 OCR 缓存中自动匹配
        $confidence = null;
        $extractMethod = 'manual';

        if ($value === '') {
            $cached = $this->getFieldFromCache($documentId, $fieldKey);
            if ($cached) {
                $value = $cached['value'];
                $confidence = $cached['confidence'];
                $extractMethod = 'auto_ocr';
            }
        }

        return DocumentField::create([
            'document_id' => $documentId,
            'field_template_id' => $template?->id,
            'field_key' => $fieldKey,
            'field_value' => $value,
            'confidence' => $confidence,
            'extract_method' => $extractMethod,
            'is_confirmed' => $extractMethod === 'manual',
            'confirmed_by' => $extractMethod === 'manual' ? $userId : null,
            'confirmed_at' => $extractMethod === 'manual' ? now() : null,
        ]);
    }

    /**
     * 从 OCR 缓存中获取字段值
     */
    private function getFieldFromCache(int $documentId, string $fieldKey): ?array
    {
        // 优先从 Python OCR 缓存服务获取
        try {
            $response = \Illuminate\Support\Facades\Http::timeout(5)
                ->get(config('services.python_ocr.url') . "/api/ocr/cache/{$documentId}");

            if ($response->successful()) {
                $data = $response->json();
                if ($data['cached'] && isset($data['data'][$fieldKey])) {
                    return $data['data'][$fieldKey];
                }
            }
        } catch (\Throwable $e) {
            // 缓存服务不可用，忽略
        }

        // Fallback: 直接查数据库缓存表
        $cache = DB::table('ocr_cache')
            ->where('document_id', $documentId)
            ->where('expires_at', '>', now())
            ->first();

        if ($cache) {
            $result = json_decode($cache->raw_result, true);
            foreach ($result['fields'] ?? [] as $field) {
                if ($field['field_key'] === $fieldKey && !empty($field['field_value'])) {
                    return [
                        'value' => $field['field_value'],
                        'confidence' => $field['confidence'] ?? 0,
                    ];
                }
            }
        }

        return null;
    }
}
