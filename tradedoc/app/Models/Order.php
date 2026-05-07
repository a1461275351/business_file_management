<?php

declare(strict_types=1);

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasMany;

class Order extends Model
{
    protected $fillable = [
        'order_no', 'order_type', 'customer_id', 'total_amount', 'currency',
        'trade_terms', 'payment_terms', 'destination_country',
        'port_of_loading', 'port_of_discharge', 'status',
        'assigned_to', 'remarks', 'created_by',
    ];

    protected $casts = [
        'total_amount' => 'decimal:2',
    ];

    public function customer(): BelongsTo
    {
        return $this->belongsTo(Customer::class);
    }

    public function documents(): HasMany
    {
        return $this->hasMany(Document::class);
    }
}
