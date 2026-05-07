<?php

declare(strict_types=1);

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\Order;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

class OrderController extends Controller
{
    public function index(Request $request): JsonResponse
    {
        $query = Order::with(['customer:id,company_name']);

        if ($keyword = $request->keyword) {
            $query->where(fn ($q) => $q->where('order_no', 'like', "%{$keyword}%"));
        }
        if ($status = $request->status) {
            $query->where('status', $status);
        }
        if ($customerId = $request->customer_id) {
            $query->where('customer_id', $customerId);
        }

        $query->withCount('documents');

        return response()->json(
            $query->orderByDesc('created_at')->paginate((int) $request->get('per_page', 20))
        );
    }

    public function show(string $id): JsonResponse
    {
        $order = Order::with(['customer', 'documents.documentType'])->withCount('documents')->findOrFail($id);
        return response()->json(['data' => $order]);
    }

    public function store(Request $request): JsonResponse
    {
        $data = $request->validate([
            'order_no' => 'required|string|max:50|unique:orders,order_no',
            'order_type' => 'required|in:export,import',
            'customer_id' => 'nullable|integer|exists:customers,id',
            'total_amount' => 'nullable|numeric',
            'currency' => 'nullable|string|max:10',
            'trade_terms' => 'nullable|string|max:20',
            'payment_terms' => 'nullable|string|max:100',
            'destination_country' => 'nullable|string|max:50',
            'port_of_loading' => 'nullable|string|max:100',
            'port_of_discharge' => 'nullable|string|max:100',
            'remarks' => 'nullable|string',
        ]);

        $data['status'] = 'draft';
        $data['created_by'] = $request->user()->id;
        $data['assigned_to'] = $request->user()->id;

        $order = Order::create($data);
        return response()->json(['message' => '订单已创建', 'data' => $order], 201);
    }

    public function update(string $id, Request $request): JsonResponse
    {
        $order = Order::findOrFail($id);

        $data = $request->validate([
            'order_no' => "sometimes|string|max:50|unique:orders,order_no,{$id}",
            'order_type' => 'sometimes|in:export,import',
            'customer_id' => 'nullable|integer|exists:customers,id',
            'total_amount' => 'nullable|numeric',
            'currency' => 'nullable|string|max:10',
            'trade_terms' => 'nullable|string|max:20',
            'payment_terms' => 'nullable|string|max:100',
            'destination_country' => 'nullable|string|max:50',
            'status' => 'sometimes|in:draft,confirmed,shipping,completed,cancelled',
            'remarks' => 'nullable|string',
        ]);

        $order->update($data);
        return response()->json(['message' => '订单已更新', 'data' => $order->fresh()]);
    }

    public function destroy(string $id): JsonResponse
    {
        Order::findOrFail($id)->delete();
        return response()->json(['message' => '订单已删除']);
    }

    // 简单列表（下拉选择用）
    public function options(): JsonResponse
    {
        $orders = Order::select('id', 'order_no', 'customer_id', 'status')
            ->orderByDesc('created_at')->limit(100)->get();
        return response()->json(['data' => $orders]);
    }
}
