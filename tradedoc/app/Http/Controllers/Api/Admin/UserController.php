<?php

declare(strict_types=1);

namespace App\Http\Controllers\Api\Admin;

use App\Http\Controllers\Controller;
use App\Models\User;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Hash;

class UserController extends Controller
{
    public function store(Request $request): JsonResponse
    {
        $data = $request->validate([
            'username' => 'required|string|max:50|unique:users,username',
            'password' => 'required|string|min:6',
            'real_name' => 'required|string|max:50',
            'email' => 'nullable|email|unique:users,email',
            'phone' => 'nullable|string|max:20',
            'department_id' => 'nullable|integer',
            'role' => 'required|string|exists:roles,name',
        ]);

        $user = User::create([
            'username' => $data['username'],
            'password' => Hash::make($data['password']),
            'real_name' => $data['real_name'],
            'email' => $data['email'] ?? null,
            'phone' => $data['phone'] ?? null,
            'department_id' => $data['department_id'] ?? null,
            'status' => 1,
        ]);

        $user->assignRole($data['role']);

        return response()->json(['message' => '用户已创建', 'data' => $user], 201);
    }

    public function update(string $id, Request $request): JsonResponse
    {
        $user = User::findOrFail($id);

        $data = $request->validate([
            'real_name' => 'sometimes|string|max:50',
            'email' => "nullable|email|unique:users,email,{$id}",
            'phone' => 'nullable|string|max:20',
            'department_id' => 'nullable|integer',
            'status' => 'sometimes|in:0,1',
            'role' => 'sometimes|string|exists:roles,name',
            'password' => 'nullable|string|min:6',
        ]);

        if (!empty($data['password'])) {
            $data['password'] = Hash::make($data['password']);
        } else {
            unset($data['password']);
        }

        if (isset($data['role'])) {
            $user->syncRoles([$data['role']]);
            unset($data['role']);
        }

        $user->update($data);

        return response()->json(['message' => '用户已更新', 'data' => $user->fresh()->load('roles')]);
    }

    public function destroy(string $id, Request $request): JsonResponse
    {
        if ((int) $id === $request->user()->id) {
            return response()->json(['message' => '不能删除自己'], 422);
        }

        User::findOrFail($id)->delete();
        return response()->json(['message' => '用户已删除']);
    }

    public function roles(): JsonResponse
    {
        $roles = \Spatie\Permission\Models\Role::select('id', 'name', 'display_name')->get();
        return response()->json(['data' => $roles]);
    }
}
