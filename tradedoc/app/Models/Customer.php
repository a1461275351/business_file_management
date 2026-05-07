<?php

declare(strict_types=1);

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsToMany;
use Illuminate\Database\Eloquent\Relations\HasMany;

class Customer extends Model
{
    protected $fillable = [
        'type', 'company_name', 'company_name_en', 'short_name',
        'country', 'contact_person', 'contact_phone', 'contact_email',
        'address', 'bank_name', 'bank_account', 'swift_code', 'tax_id',
        'remarks', 'status', 'created_by',
    ];

    public function orders(): HasMany
    {
        return $this->hasMany(Order::class);
    }

    public function documents(): HasMany
    {
        return $this->hasMany(Document::class);
    }

    public function assignedUsers(): BelongsToMany
    {
        return $this->belongsToMany(User::class, 'user_customers');
    }
}
