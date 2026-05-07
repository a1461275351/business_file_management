<?php

declare(strict_types=1);

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\HasMany;

class DocumentType extends Model
{
    protected $fillable = ['code', 'name', 'name_en', 'icon', 'color', 'sort_order', 'status'];

    public $timestamps = false;

    protected $casts = [
        'status' => 'integer',
        'sort_order' => 'integer',
    ];

    public function documents(): HasMany
    {
        return $this->hasMany(Document::class);
    }

    public function fieldTemplates(): HasMany
    {
        return $this->hasMany(FieldTemplate::class);
    }
}
