<?php

declare(strict_types=1);

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class FieldTemplate extends Model
{
    protected $fillable = [
        'document_type_id', 'field_key', 'field_name', 'field_name_en',
        'field_type', 'is_required', 'is_auto_extract', 'extract_rule',
        'validation_rule', 'enum_options', 'sort_order', 'status',
    ];

    protected $casts = [
        'is_required' => 'boolean',
        'is_auto_extract' => 'boolean',
        'enum_options' => 'json',
    ];

    public function documentType(): BelongsTo
    {
        return $this->belongsTo(DocumentType::class);
    }
}
