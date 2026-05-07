<?php

declare(strict_types=1);

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\Notification;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

class NotificationController extends Controller
{
    /**
     * 当前用户的通知列表
     */
    public function index(Request $request): JsonResponse
    {
        $query = Notification::where('user_id', $request->user()->id);

        if ($request->has('unread_only') && $request->unread_only) {
            $query->where('is_read', false);
        }

        $notifications = $query->orderByDesc('created_at')
            ->paginate((int) $request->get('per_page', 20));

        return response()->json($notifications);
    }

    /**
     * 未读数量
     */
    public function unreadCount(Request $request): JsonResponse
    {
        $count = Notification::where('user_id', $request->user()->id)
            ->where('is_read', false)
            ->count();

        return response()->json(['data' => ['count' => $count]]);
    }

    /**
     * 标记已读
     */
    public function markRead(string $id, Request $request): JsonResponse
    {
        Notification::where('id', $id)
            ->where('user_id', $request->user()->id)
            ->update(['is_read' => true, 'read_at' => now()]);

        return response()->json(['message' => '已标记已读']);
    }

    /**
     * 全部标记已读
     */
    public function markAllRead(Request $request): JsonResponse
    {
        Notification::where('user_id', $request->user()->id)
            ->where('is_read', false)
            ->update(['is_read' => true, 'read_at' => now()]);

        return response()->json(['message' => '全部已标记已读']);
    }
}
