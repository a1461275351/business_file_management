<?php

declare(strict_types=1);

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class OperationLog extends Model
{
    public $timestamps = false;

    protected $fillable = [
        'user_id', 'module', 'action', 'target_type', 'target_id',
        'description', 'ip_address', 'user_agent', 'extra_data',
    ];

    protected $casts = [
        'extra_data' => 'json',
        'created_at' => 'datetime',
    ];

    public function user(): BelongsTo
    {
        return $this->belongsTo(User::class);
    }

    // 快捷记录方法
    public static function log(
        string $module, string $action, string $description,
        ?string $targetType = null, ?int $targetId = null,
        ?array $extra = null
    ): void {
        $user = auth()->user();
        $request = request();

        self::create([
            'user_id' => $user?->id,
            'module' => $module,
            'action' => $action,
            'target_type' => $targetType,
            'target_id' => $targetId,
            'description' => $description,
            'ip_address' => $request?->ip(),
            'user_agent' => substr($request?->userAgent() ?? '', 0, 300),
            'extra_data' => $extra,
            'created_at' => now(),
        ]);
    }
}
