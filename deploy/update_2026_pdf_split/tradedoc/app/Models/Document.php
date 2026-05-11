<?php

declare(strict_types=1);

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasMany;
use Illuminate\Database\Eloquent\SoftDeletes;

class Document extends Model
{
    use SoftDeletes;

    protected $fillable = [
        'doc_no', 'document_type_id', 'order_id', 'customer_id',
        'parent_document_id', 'split_page_range', 'is_split_container',
        'title', 'original_filename', 'storage_path', 'file_size', 'file_ext',
        'mime_type', 'file_hash', 'total_amount', 'currency', 'trade_date',
        'language', 'ocr_confidence', 'field_complete_rate', 'version',
        'status', 'uploaded_by', 'reviewed_by', 'reviewed_at',
        'approved_by', 'approved_at', 'archived_at',
    ];

    protected $casts = [
        'file_size' => 'integer',
        'total_amount' => 'decimal:2',
        'ocr_confidence' => 'decimal:2',
        'field_complete_rate' => 'decimal:2',
        'version' => 'integer',
        'is_split_container' => 'boolean',
        'trade_date' => 'date',
        'reviewed_at' => 'datetime',
        'approved_at' => 'datetime',
        'archived_at' => 'datetime',
    ];

    public function parent(): BelongsTo
    {
        return $this->belongsTo(Document::class, 'parent_document_id');
    }

    public function children(): HasMany
    {
        return $this->hasMany(Document::class, 'parent_document_id');
    }

    public function documentType(): BelongsTo
    {
        return $this->belongsTo(DocumentType::class);
    }

    public function order(): BelongsTo
    {
        return $this->belongsTo(Order::class);
    }

    public function customer(): BelongsTo
    {
        return $this->belongsTo(Customer::class);
    }

    public function uploader(): BelongsTo
    {
        return $this->belongsTo(User::class, 'uploaded_by');
    }

    public function reviewer(): BelongsTo
    {
        return $this->belongsTo(User::class, 'reviewed_by');
    }

    public function approver(): BelongsTo
    {
        return $this->belongsTo(User::class, 'approved_by');
    }

    public function fields(): HasMany
    {
        return $this->hasMany(DocumentField::class);
    }

    public function versions(): HasMany
    {
        return $this->hasMany(DocumentVersion::class);
    }

    public function ocrTasks(): HasMany
    {
        return $this->hasMany(OcrTask::class);
    }

    // 生成文件编号
    public static function generateDocNo(string $typeCode): string
    {
        $prefix = match ($typeCode) {
            'customs_declaration' => 'D',
            'commercial_invoice' => 'INV',
            'packing_list' => 'PL',
            'bank_receipt' => 'BK',
            'bill_of_lading' => 'BL',
            'certificate_of_origin' => 'CO',
            'contract' => 'CT',
            'letter_of_credit' => 'LC',
            default => 'DOC',
        };

        $date = now()->format('ymd');
        $pattern = $prefix . $date . '-%';

        // 查当天最大序号（含软删除的），避免编号冲突
        $maxNo = self::withTrashed()
            ->where('doc_no', 'like', $pattern)
            ->orderByDesc('doc_no')
            ->value('doc_no');

        if ($maxNo && preg_match('/-(\d+)$/', $maxNo, $m)) {
            $seq = (int) $m[1] + 1;
        } else {
            $seq = 1;
        }

        return sprintf('%s%s-%04d', $prefix, $date, $seq);
    }
}
