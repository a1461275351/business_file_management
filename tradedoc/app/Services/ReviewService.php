<?php

declare(strict_types=1);

namespace App\Services;

use App\Models\Document;
use App\Models\DocumentField;
use App\Models\ReviewTask;
use Illuminate\Support\Facades\DB;

class ReviewService
{
    /**
     * 获取待核对任务列表
     */
    public function listTasks(array $filters, int $perPage = 20)
    {
        $query = ReviewTask::with([
            'document' => fn ($q) => $q->select('id', 'doc_no', 'document_type_id', 'original_filename', 'order_id', 'total_amount', 'currency')
                ->with(['documentType:id,name,color', 'order:id,order_no']),
            'assignee:id,real_name',
        ]);

        if (!empty($filters['status'])) {
            $query->where('status', $filters['status']);
        } else {
            $query->whereIn('status', ['pending', 'assigned', 'in_progress']);
        }

        if (!empty($filters['priority'])) {
            $query->where('priority', $filters['priority']);
        }

        if (!empty($filters['assigned_to'])) {
            $query->where('assigned_to', $filters['assigned_to']);
        }

        return $query->orderByRaw("FIELD(priority, 'urgent', 'medium', 'normal')")
            ->orderBy('created_at')
            ->paginate($perPage);
    }

    /**
     * 获取核对任务详情（含需核对的字段和文件信息）
     */
    public function taskDetail(int $taskId): array
    {
        $task = ReviewTask::with([
            'document.documentType',
            'document.uploader:id,real_name',
            'document.order:id,order_no',
            'assignee:id,real_name',
        ])->findOrFail($taskId);

        // 获取需核对的字段（低置信度字段）
        $fields = DocumentField::where('document_id', $task->document_id)
            ->with('template:id,field_name,field_name_en,field_type,is_required')
            ->orderBy('confidence')
            ->get();

        return [
            'task' => $task,
            'fields' => $fields,
        ];
    }

    /**
     * 批量确认字段
     */
    public function confirmFields(int $taskId, array $fieldUpdates, int $userId): ReviewTask
    {
        return DB::transaction(function () use ($taskId, $fieldUpdates, $userId) {
            $task = ReviewTask::findOrFail($taskId);

            // 更新每个字段
            foreach ($fieldUpdates as $update) {
                $field = DocumentField::findOrFail($update['field_id']);

                $field->update([
                    'field_value' => $update['value'],
                    'is_confirmed' => true,
                    'confirmed_by' => $userId,
                    'confirmed_at' => now(),
                    'extract_method' => $field->extract_method === 'auto_ocr' ? 'auto_ocr' : 'manual',
                ]);
            }

            // 完成任务
            $task->update([
                'status' => 'completed',
                'completed_at' => now(),
            ]);

            // 检查文件是否所有低置信度字段都已确认
            $unconfirmedCount = DocumentField::where('document_id', $task->document_id)
                ->where('is_confirmed', false)
                ->where('confidence', '<', 80)
                ->count();

            if ($unconfirmedCount === 0) {
                Document::where('id', $task->document_id)
                    ->update(['status' => 'pending_approval']);
            }

            return $task->fresh();
        });
    }

    /**
     * 跳过任务（转派）
     */
    public function skipTask(int $taskId, int $userId): ReviewTask
    {
        $task = ReviewTask::findOrFail($taskId);
        $task->update([
            'status' => 'pending',
            'assigned_to' => null,
            'transferred_from' => $userId,
        ]);

        return $task->fresh();
    }

    /**
     * 自动为文件创建核对任务
     */
    public function createTaskForDocument(int $documentId): ?ReviewTask
    {
        // 查找低置信度字段
        $lowConfidenceFields = DocumentField::where('document_id', $documentId)
            ->where('confidence', '<', 80)
            ->where('is_confirmed', false)
            ->pluck('id')
            ->toArray();

        if (empty($lowConfidenceFields)) {
            return null;
        }

        // 判断优先级
        $minConfidence = DocumentField::where('document_id', $documentId)
            ->where('is_confirmed', false)
            ->min('confidence');

        $priority = match (true) {
            $minConfidence < 50 => 'urgent',
            $minConfidence < 70 => 'medium',
            default => 'normal',
        };

        return ReviewTask::create([
            'document_id' => $documentId,
            'field_ids' => $lowConfidenceFields,
            'priority' => $priority,
            'status' => 'pending',
            'timeout_at' => now()->addHours(4),
        ]);
    }

    /**
     * 统计概览
     */
    public function statistics(): array
    {
        return [
            'pending' => ReviewTask::where('status', 'pending')->count(),
            'in_progress' => ReviewTask::whereIn('status', ['assigned', 'in_progress'])->count(),
            'completed_today' => ReviewTask::where('status', 'completed')
                ->whereDate('completed_at', today())->count(),
            'urgent' => ReviewTask::where('priority', 'urgent')
                ->whereIn('status', ['pending', 'assigned', 'in_progress'])->count(),
        ];
    }
}
