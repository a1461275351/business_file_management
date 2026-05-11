<?php

declare(strict_types=1);

namespace App\Http\Controllers\Api;

use App\Exports\DocumentsExport;
use App\Exports\SingleDocumentExport;
use App\Http\Controllers\Controller;
use App\Models\DocumentType;
use App\Services\DocumentService;
use Illuminate\Http\JsonResponse;
use Maatwebsite\Excel\Facades\Excel;
use Illuminate\Http\Request;

class DocumentController extends Controller
{
    public function __construct(
        private readonly DocumentService $documentService,
    ) {}

    /**
     * 获取文件类型列表（上传时选择用）
     */
    public function types(): JsonResponse
    {
        $types = DocumentType::where('status', 1)
            ->orderBy('sort_order')
            ->get(['id', 'code', 'name', 'name_en', 'icon', 'color']);

        return response()->json(['data' => $types]);
    }

    /**
     * 上传文件
     */
    public function upload(Request $request): JsonResponse
    {
        $request->validate([
            'file' => 'required|file|max:51200', // 50MB
            'document_type_id' => 'required|integer|exists:document_types,id',
            'order_id' => 'nullable|integer|exists:orders,id',
            'customer_id' => 'nullable|integer|exists:customers,id',
        ]);

        $document = $this->documentService->upload(
            file: $request->file('file'),
            typeId: (int) $request->document_type_id,
            userId: (int) $request->user()->id,
            orderId: $request->order_id ? (int) $request->order_id : null,
            customerId: $request->customer_id ? (int) $request->customer_id : null,
        );

        // 自动提交 OCR 任务
        $ocrTask = $this->documentService->submitOcr($document);

        $document->load('documentType');

        return response()->json([
            'message' => '文件上传成功，已提交 OCR 识别',
            'data' => [
                'document' => $document,
                'ocr_task_id' => $ocrTask->id,
            ],
        ], 201);
    }

    /**
     * 批量上传
     */
    public function batchUpload(Request $request): JsonResponse
    {
        $request->validate([
            'files' => 'required|array|min:1|max:50',
            'files.*' => 'file|max:51200',
            'document_type_id' => 'required|integer|exists:document_types,id',
            'order_id' => 'nullable|integer|exists:orders,id',
        ]);

        $documents = $this->documentService->batchUpload(
            files: $request->file('files'),
            typeId: (int) $request->document_type_id,
            userId: (int) $request->user()->id,
            orderId: $request->order_id ? (int) $request->order_id : null,
        );

        // 逐个提交 OCR
        foreach ($documents as $doc) {
            $this->documentService->submitOcr($doc);
        }

        return response()->json([
            'message' => sprintf('%d 个文件上传成功', count($documents)),
            'data' => ['count' => count($documents)],
        ], 201);
    }

    /**
     * 分析 PDF 是否需要拆分（上传后立即调用）
     * GET /api/v1/documents/{id}/analyze-split
     */
    public function analyzeSplit(string $id): JsonResponse
    {
        $document = \App\Models\Document::findOrFail($id);
        $result = $this->documentService->analyzeSplit($document);

        if (empty($result['success'])) {
            return response()->json([
                'message' => '分析失败',
                'error' => $result['error'] ?? 'unknown',
            ], 500);
        }

        return response()->json(['data' => $result['data']]);
    }

    /**
     * 执行拆分（用户在前端确认拆分方案后调用）
     * POST /api/v1/documents/{id}/execute-split
     * body: { "segments": [{ "type_code": "...", "page_start": 1, "page_end": 2 }, ...] }
     */
    public function executeSplit(Request $request, string $id): JsonResponse
    {
        $request->validate([
            'segments' => 'required|array|min:1',
            'segments.*.type_code' => 'required|string',
            'segments.*.page_start' => 'required|integer|min:1',
            'segments.*.page_end' => 'required|integer|min:1',
        ]);

        $parent = \App\Models\Document::findOrFail($id);
        $result = $this->documentService->executeSplit(
            $parent,
            $request->input('segments'),
            (int) ($request->user()?->id ?? $parent->uploaded_by),
        );

        if (empty($result['success'])) {
            return response()->json([
                'message' => '拆分失败',
                'errors' => $result['errors'] ?? [],
            ], 500);
        }

        return response()->json([
            'message' => '拆分完成',
            'data' => [
                'parent_id' => $parent->id,
                'children' => collect($result['children'])->map(fn($c) => [
                    'id' => $c->id,
                    'doc_no' => $c->doc_no,
                    'document_type_id' => $c->document_type_id,
                    'split_page_range' => $c->split_page_range,
                    'status' => $c->status,
                ])->all(),
                'errors' => $result['errors'] ?? [],
            ],
        ]);
    }

    /**
     * 文件列表
     */
    public function index(Request $request): JsonResponse
    {
        $filters = $request->only([
            'document_type_id', 'status', 'keyword',
            'date_from', 'date_to', 'customer_id', 'order_id',
            'parent_document_id',
        ]);

        $perPage = (int) $request->get('per_page', 20);
        $result = $this->documentService->list($filters, $perPage);

        return response()->json($result);
    }

    /**
     * 文件详情
     */
    public function show(string $id): JsonResponse
    {
        $document = $this->documentService->detail($id);

        return response()->json(['data' => $document]);
    }

    /**
     * 仪表盘统计
     */
    public function statistics(): JsonResponse
    {
        $stats = $this->documentService->statistics();

        return response()->json(['data' => $stats]);
    }

    /**
     * 数据报表
     */
    public function reports(Request $request): JsonResponse
    {
        $totalDocs = \App\Models\Document::count();
        $archivedCount = \App\Models\Document::where('status', 'archived')->count();
        $avgConfidence = (float) (\Illuminate\Support\Facades\DB::table('document_fields')
            ->whereNotNull('confidence')->where('confidence', '>', 0)->avg('confidence') ?? 0);
        $totalFields = \Illuminate\Support\Facades\DB::table('document_fields')->count();

        $typeDistribution = \Illuminate\Support\Facades\DB::table('documents')
            ->join('document_types', 'documents.document_type_id', '=', 'document_types.id')
            ->whereNull('documents.deleted_at')
            ->select('document_types.name', 'document_types.color', \Illuminate\Support\Facades\DB::raw('count(*) as count'))
            ->groupBy('document_types.name', 'document_types.color')->get();

        $statusDistribution = \Illuminate\Support\Facades\DB::table('documents')
            ->whereNull('deleted_at')
            ->select('status', \Illuminate\Support\Facades\DB::raw('count(*) as count'))
            ->groupBy('status')->get();

        $monthlyTrend = \Illuminate\Support\Facades\DB::table('documents')
            ->whereNull('deleted_at')
            ->where('created_at', '>=', now()->subMonths(6))
            ->select(\Illuminate\Support\Facades\DB::raw("DATE_FORMAT(created_at, '%Y-%m') as month"), \Illuminate\Support\Facades\DB::raw('count(*) as count'))
            ->groupBy('month')->orderBy('month')->get();

        return response()->json(['data' => [
            'total_documents' => $totalDocs,
            'archived_count' => $archivedCount,
            'avg_confidence' => round($avgConfidence, 1),
            'total_fields' => $totalFields,
            'type_distribution' => $typeDistribution,
            'status_distribution' => $statusDistribution,
            'monthly_trend' => $monthlyTrend,
        ]]);
    }

    /**
     * 删除文件（软删除）
     */
    public function destroy(string $id, Request $request): JsonResponse
    {
        $this->documentService->delete($id, (int) $request->user()->id);

        return response()->json(['message' => '文件已删除']);
    }

    /**
     * 变更文件状态
     */
    public function changeStatus(string $id, Request $request): JsonResponse
    {
        $request->validate(['status' => 'required|string|in:ocr_processing,pending_review,pending_approval,archived,voided']);

        try {
            $document = $this->documentService->changeStatus(
                $id, $request->status, (int) $request->user()->id
            );
            return response()->json(['message' => '状态已更新', 'data' => $document]);
        } catch (\InvalidArgumentException $e) {
            return response()->json(['message' => $e->getMessage()], 422);
        }
    }

    /**
     * 下载文件原件
     */
    public function download(string $id): \Symfony\Component\HttpFoundation\BinaryFileResponse
    {
        $fileInfo = $this->documentService->getFilePath($id);

        return response()->download($fileInfo['path'], $fileInfo['filename'], [
            'Content-Type' => $fileInfo['mime_type'],
        ]);
    }

    /**
     * 在线预览文件（图片直接输出，PDF 通过浏览器展示）
     */
    public function preview(string $id): \Symfony\Component\HttpFoundation\BinaryFileResponse
    {
        $fileInfo = $this->documentService->getFilePath($id);

        return response()->file($fileInfo['path'], [
            'Content-Type' => $fileInfo['mime_type'],
        ]);
    }

    /**
     * 更新字段值
     */
    public function updateField(Request $request): JsonResponse
    {
        $request->validate([
            'field_id' => 'required|integer|exists:document_fields,id',
            'value' => 'nullable|string',
        ]);

        $field = $this->documentService->updateField(
            (int) $request->field_id, $request->value ?? '', (int) $request->user()->id
        );

        return response()->json(['message' => '字段已更新', 'data' => $field]);
    }

    /**
     * OCR 缓存代理（前端通过 PHP 调 Python，避免 CORS）
     */
    public function ocrCache(string $id): JsonResponse
    {
        try {
            $response = \Illuminate\Support\Facades\Http::timeout(5)
                ->get(config('services.python_ocr.url') . "/api/ocr/cache/{$id}");
            return response()->json($response->json());
        } catch (\Throwable $e) {
            return response()->json(['cached' => false, 'data' => null]);
        }
    }

    /**
     * 重新 OCR 识别
     */
    public function reOcr(Request $request): JsonResponse
    {
        $request->validate(['document_id' => 'required|integer|exists:documents,id']);

        $documentId = (int) $request->document_id;
        $document = \App\Models\Document::with('documentType')->findOrFail($documentId);

        // 创建新的 OCR 任务
        \App\Models\OcrTask::create([
            'document_id' => $documentId,
            'task_type' => 'ocr',
            'status' => 'pending',
            'priority' => 3, // 高优先级
            'retry_count' => 0,
            'max_retries' => 3,
        ]);

        // 调用 Python OCR 服务
        $ocrService = app(\App\Services\OcrService::class);
        $result = $ocrService->processDocument($documentId, $document->documentType?->code ?? '');

        if (!empty($result['success'])) {
            return response()->json([
                'message' => '识别完成',
                'data' => $result,
            ]);
        }

        return response()->json([
            'message' => $result['error'] ?? '识别失败',
        ], 500);
    }

    /**
     * 删除字段
     */
    public function deleteField(string $fieldId): JsonResponse
    {
        $field = \App\Models\DocumentField::findOrFail($fieldId);
        $field->delete();

        return response()->json(['message' => '字段已删除']);
    }

    /**
     * 手动添加字段
     */
    public function addField(Request $request): JsonResponse
    {
        $request->validate([
            'document_id' => 'required|integer|exists:documents,id',
            'field_key' => 'required|string|max:50',
            'field_name' => 'nullable|string|max:50',
            'field_value' => 'nullable|string',
        ]);

        $field = $this->documentService->addField(
            (int) $request->document_id,
            $request->field_key,
            $request->field_value ?? '',
            (int) $request->user()->id,
            $request->field_name ?? '',
        );

        return response()->json(['message' => '字段已添加', 'data' => $field], 201);
    }

    /**
     * 批量导出 Excel
     */
    public function export(Request $request)
    {
        $ids = $request->input('ids', []);
        $filters = $request->only(['document_type_id', 'status', 'date_from', 'date_to']);

        $filename = '文件数据导出_' . now()->format('Ymd_His') . '.xlsx';

        return Excel::download(new DocumentsExport($ids, $filters), $filename);
    }

    /**
     * 单个文件导出 Excel（含所有提取字段）
     */
    public function exportSingle(string $id)
    {
        $document = \App\Models\Document::with(['documentType', 'fields.template'])->findOrFail($id);
        $filename = $document->doc_no . '_字段数据.xlsx';

        return Excel::download(new SingleDocumentExport($document), $filename);
    }
}
