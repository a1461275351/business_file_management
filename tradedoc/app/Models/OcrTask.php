<?php

declare(strict_types=1);

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class OcrTask extends Model
{
    protected $fillable = [
        'document_id', 'task_type', 'status', 'priority',
        'retry_count', 'max_retries', 'started_at', 'completed_at',
        'result_summary', 'error_message', 'worker_id',
    ];

    protected $casts = [
        'result_summary' => 'json',
        'started_at' => 'datetime',
        'completed_at' => 'datetime',
    ];

    public function document(): BelongsTo
    {
        return $this->belongsTo(Document::class);
    }
}
