<?php

declare(strict_types=1);

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class ReviewTask extends Model
{
    protected $fillable = [
        'document_id', 'field_ids', 'priority', 'status',
        'assigned_to', 'assigned_at', 'started_at', 'completed_at',
        'timeout_at', 'transferred_from', 'remarks',
    ];

    protected $casts = [
        'field_ids' => 'json',
        'assigned_at' => 'datetime',
        'started_at' => 'datetime',
        'completed_at' => 'datetime',
        'timeout_at' => 'datetime',
    ];

    public function document(): BelongsTo
    {
        return $this->belongsTo(Document::class);
    }

    public function assignee(): BelongsTo
    {
        return $this->belongsTo(User::class, 'assigned_to');
    }
}
