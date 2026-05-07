<?php

declare(strict_types=1);

use App\Http\Controllers\Api\AuthController;
use App\Http\Controllers\Api\DocumentController;
use App\Http\Controllers\Api\NotificationController;
use App\Http\Controllers\Api\ReviewController;
use Illuminate\Support\Facades\Route;

Route::prefix('v1')->group(function () {

    // 认证
    Route::post('/auth/login', [AuthController::class, 'login']);

    // 文件预览/下载/导出（内部系统，无需严格认证）
    Route::get('/documents/{id}/preview', [DocumentController::class, 'preview'])->where('id', '[0-9]+');
    Route::get('/documents/{id}/download', [DocumentController::class, 'download'])->where('id', '[0-9]+');
    Route::get('/documents/{id}/export', [DocumentController::class, 'exportSingle'])->where('id', '[0-9]+');
    Route::get('/documents/export', [DocumentController::class, 'export']);

    // 需要登录
    Route::middleware('auth:sanctum')->group(function () {
        // 认证
        Route::get('/auth/me', [AuthController::class, 'me']);
        Route::post('/auth/logout', [AuthController::class, 'logout']);

        // 文件类型
        Route::get('/document-types', [DocumentController::class, 'types']);

        // 文件管理
        Route::post('/documents/upload', [DocumentController::class, 'upload']);
        Route::post('/documents/batch-upload', [DocumentController::class, 'batchUpload']);
        Route::get('/documents/statistics', [DocumentController::class, 'statistics']);
        Route::post('/documents/update-field', [DocumentController::class, 'updateField']);
        Route::post('/documents/add-field', [DocumentController::class, 'addField']);
        Route::delete('/documents/fields/{fieldId}', [DocumentController::class, 'deleteField'])->where('fieldId', '[0-9]+');
        Route::post('/documents/re-ocr', [DocumentController::class, 'reOcr']);
        Route::get('/documents/{id}/ocr-cache', [DocumentController::class, 'ocrCache'])->where('id', '[0-9]+');

        // OCR 引擎状态代理
        Route::get('/ocr/engine-status', function () {
            try {
                $res = \Illuminate\Support\Facades\Http::timeout(3)->get(config('services.python_ocr.url') . '/api/ocr/engine-status');
                return response()->json($res->json());
            } catch (\Throwable $e) {
                return response()->json(['engine_mode' => 'offline', 'api_key_set' => false, 'model_loaded' => false]);
            }
        });
        Route::get('/documents', [DocumentController::class, 'index']);
        // 导出已移到认证外
        Route::get('/documents/{id}', [DocumentController::class, 'show'])->where('id', '[0-9]+');
        Route::delete('/documents/{id}', [DocumentController::class, 'destroy'])->where('id', '[0-9]+');
        Route::put('/documents/{id}/status', [DocumentController::class, 'changeStatus'])->where('id', '[0-9]+');
        // 预览/下载已移到认证外

        // 人工核对
        Route::get('/reviews', [ReviewController::class, 'index']);
        Route::get('/reviews/statistics', [ReviewController::class, 'statistics']);
        Route::get('/reviews/{id}', [ReviewController::class, 'show'])->where('id', '[0-9]+');
        Route::post('/reviews/{id}/confirm', [ReviewController::class, 'confirm'])->where('id', '[0-9]+');
        Route::post('/reviews/{id}/skip', [ReviewController::class, 'skip'])->where('id', '[0-9]+');

        // 通知
        Route::get('/notifications', [NotificationController::class, 'index']);
        Route::get('/notifications/unread-count', [NotificationController::class, 'unreadCount']);
        Route::put('/notifications/{id}/read', [NotificationController::class, 'markRead'])->where('id', '[0-9]+');
        Route::put('/notifications/read-all', [NotificationController::class, 'markAllRead']);

        // 订单管理
        Route::get('/orders/options', [\App\Http\Controllers\Api\OrderController::class, 'options']);
        Route::get('/orders', [\App\Http\Controllers\Api\OrderController::class, 'index']);
        Route::get('/orders/{id}', [\App\Http\Controllers\Api\OrderController::class, 'show'])->where('id', '[0-9]+');
        Route::post('/orders', [\App\Http\Controllers\Api\OrderController::class, 'store']);
        Route::put('/orders/{id}', [\App\Http\Controllers\Api\OrderController::class, 'update'])->where('id', '[0-9]+');
        Route::delete('/orders/{id}', [\App\Http\Controllers\Api\OrderController::class, 'destroy'])->where('id', '[0-9]+');

        // 客户管理
        Route::get('/customers/options', [\App\Http\Controllers\Api\CustomerController::class, 'options']);
        Route::get('/customers', [\App\Http\Controllers\Api\CustomerController::class, 'index']);
        Route::get('/customers/{id}', [\App\Http\Controllers\Api\CustomerController::class, 'show'])->where('id', '[0-9]+');
        Route::post('/customers', [\App\Http\Controllers\Api\CustomerController::class, 'store']);
        Route::put('/customers/{id}', [\App\Http\Controllers\Api\CustomerController::class, 'update'])->where('id', '[0-9]+');
        Route::delete('/customers/{id}', [\App\Http\Controllers\Api\CustomerController::class, 'destroy'])->where('id', '[0-9]+');

        // 报表
        Route::get('/documents/reports', [DocumentController::class, 'reports']);

        // AI 问答
        Route::post('/ai/chat', [\App\Http\Controllers\Api\AiChatController::class, 'chat']);

        // 管理后台
        Route::get('/admin/users', [\App\Http\Controllers\Api\Admin\AdminController::class, 'users']);
        Route::post('/admin/users', [\App\Http\Controllers\Api\Admin\UserController::class, 'store']);
        Route::put('/admin/users/{id}', [\App\Http\Controllers\Api\Admin\UserController::class, 'update'])->where('id', '[0-9]+');
        Route::delete('/admin/users/{id}', [\App\Http\Controllers\Api\Admin\UserController::class, 'destroy'])->where('id', '[0-9]+');
        Route::get('/admin/roles', [\App\Http\Controllers\Api\Admin\UserController::class, 'roles']);
        Route::get('/admin/field-templates/{typeId}', [\App\Http\Controllers\Api\Admin\AdminController::class, 'fieldTemplates']);
        Route::get('/admin/logs', [\App\Http\Controllers\Api\Admin\AdminController::class, 'logs']);
    });
});
