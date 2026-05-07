<?php

declare(strict_types=1);

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Services\ReviewService;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

class ReviewController extends Controller
{
    public function __construct(
        private readonly ReviewService $reviewService,
    ) {}

    /**
     * 核对任务列表
     */
    public function index(Request $request): JsonResponse
    {
        $filters = $request->only(['status', 'priority', 'assigned_to']);
        $perPage = (int) $request->get('per_page', 20);

        return response()->json(
            $this->reviewService->listTasks($filters, $perPage)
        );
    }

    /**
     * 核对任务详情
     */
    public function show(string $id): JsonResponse
    {
        $detail = $this->reviewService->taskDetail((int) $id);

        return response()->json(['data' => $detail]);
    }

    /**
     * 确认字段并完成核对
     */
    public function confirm(string $id, Request $request): JsonResponse
    {
        $request->validate([
            'fields' => 'required|array|min:1',
            'fields.*.field_id' => 'required|integer|exists:document_fields,id',
            'fields.*.value' => 'required|string',
        ]);

        $task = $this->reviewService->confirmFields(
            (int) $id,
            $request->fields,
            (int) $request->user()->id
        );

        return response()->json([
            'message' => '核对完成',
            'data' => $task,
        ]);
    }

    /**
     * 跳过/转派任务
     */
    public function skip(string $id, Request $request): JsonResponse
    {
        $task = $this->reviewService->skipTask(
            (int) $id,
            (int) $request->user()->id
        );

        return response()->json([
            'message' => '任务已转派',
            'data' => $task,
        ]);
    }

    /**
     * 核对统计
     */
    public function statistics(): JsonResponse
    {
        return response()->json([
            'data' => $this->reviewService->statistics(),
        ]);
    }
}
