<?php

declare(strict_types=1);

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\Customer;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

class CustomerController extends Controller
{
    public function index(Request $request): JsonResponse
    {
        $query = Customer::query();

        if ($keyword = $request->keyword) {
            $query->where(fn ($q) => $q
                ->where('company_name', 'like', "%{$keyword}%")
                ->orWhere('company_name_en', 'like', "%{$keyword}%")
                ->orWhere('short_name', 'like', "%{$keyword}%")
                ->orWhere('contact_person', 'like', "%{$keyword}%"));
        }
        if ($type = $request->type) {
            $query->where('type', $type);
        }
        if ($country = $request->country) {
            $query->where('country', $country);
        }

        $query->withCount('orders');

        return response()->json(
            $query->orderByDesc('created_at')->paginate((int) $request->get('per_page', 20))
        );
    }

    public function show(string $id): JsonResponse
    {
        $customer = Customer::withCount('orders')->findOrFail($id);
        // 加载最近订单
        $customer->load(['orders' => fn ($q) => $q->latest()->limit(10)]);
        return response()->json(['data' => $customer]);
    }

    public function store(Request $request): JsonResponse
    {
        $data = $request->validate([
            'type' => 'required|in:customer,supplier,both',
            'company_name' => 'required|string|max:200',
            'company_name_en' => 'nullable|string|max:200',
            'short_name' => 'nullable|string|max:50',
            'country' => 'nullable|string|max:50',
            'contact_person' => 'nullable|string|max:50',
            'contact_phone' => 'nullable|string|max:50',
            'contact_email' => 'nullable|string|max:100',
            'address' => 'nullable|string|max:500',
            'bank_name' => 'nullable|string|max:200',
            'bank_account' => 'nullable|string|max:100',
            'swift_code' => 'nullable|string|max:20',
            'tax_id' => 'nullable|string|max:50',
            'remarks' => 'nullable|string',
        ]);

        $data['status'] = 1;
        $data['created_by'] = $request->user()->id;

        $customer = Customer::create($data);
        return response()->json(['message' => '客户已创建', 'data' => $customer], 201);
    }

    public function update(string $id, Request $request): JsonResponse
    {
        $customer = Customer::findOrFail($id);

        $data = $request->validate([
            'type' => 'sometimes|in:customer,supplier,both',
            'company_name' => 'sometimes|string|max:200',
            'company_name_en' => 'nullable|string|max:200',
            'short_name' => 'nullable|string|max:50',
            'country' => 'nullable|string|max:50',
            'contact_person' => 'nullable|string|max:50',
            'contact_phone' => 'nullable|string|max:50',
            'contact_email' => 'nullable|string|max:100',
            'address' => 'nullable|string|max:500',
            'remarks' => 'nullable|string',
        ]);

        $customer->update($data);
        return response()->json(['message' => '客户已更新', 'data' => $customer->fresh()]);
    }

    public function destroy(string $id): JsonResponse
    {
        Customer::findOrFail($id)->delete();
        return response()->json(['message' => '客户已删除']);
    }

    // 简单列表（下拉选择用）
    public function options(): JsonResponse
    {
        $customers = Customer::select('id', 'company_name', 'short_name', 'type')
            ->where('status', 1)->orderBy('company_name')->get();
        return response()->json(['data' => $customers]);
    }
}
