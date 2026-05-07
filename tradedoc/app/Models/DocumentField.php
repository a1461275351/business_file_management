<?php

declare(strict_types=1);

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class DocumentField extends Model
{
    protected $fillable = [
        'document_id', 'field_template_id', 'field_key', 'field_value',
        'confidence', 'extract_method', 'bbox_info', 'is_confirmed',
        'confirmed_by', 'confirmed_at',
    ];

    protected $casts = [
        'confidence' => 'decimal:2',
        'bbox_info' => 'json',
        'is_confirmed' => 'boolean',
        'confirmed_at' => 'datetime',
    ];

    public function document(): BelongsTo
    {
        return $this->belongsTo(Document::class);
    }

    public function template(): BelongsTo
    {
        return $this->belongsTo(FieldTemplate::class, 'field_template_id');
    }
}
