<?php

declare(strict_types=1);

namespace App\Http\Controllers\Api\Admin;

use App\Http\Controllers\Controller;
use App\Models\FieldTemplate;
use App\Models\User;
use Illuminate\Http\JsonResponse;

class AdminController extends Controller
{
    /**
     * 用户列表
     */
    public function users(): JsonResponse
    {
        $users = User::with(['roles', 'department'])
            ->orderByDesc('id')
            ->get();

        return response()->json(['data' => $users]);
    }

    /**
     * 指定文件类型的字段模板
     */
    public function fieldTemplates(string $typeId): JsonResponse
    {
        $templates = FieldTemplate::where('document_type_id', $typeId)
            ->where('status', 1)
            ->orderBy('sort_order')
            ->get();

        return response()->json(['data' => $templates]);
    }

    public function logs(\Illuminate\Http\Request $request): JsonResponse
    {
        $query = \App\Models\OperationLog::with('user:id,real_name');

        if ($module = $request->module) {
            $query->where('module', $module);
        }

        return response()->json(
            $query->orderByDesc('created_at')->paginate(30)
        );
    }
}
