<?php

declare(strict_types=1);

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\User;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Hash;
use Illuminate\Validation\ValidationException;

class AuthController extends Controller
{
    public function login(Request $request): JsonResponse
    {
        $request->validate([
            'username' => 'required|string',
            'password' => 'required|string',
        ]);

        $user = User::where('username', $request->username)->first();

        if (! $user || ! Hash::check($request->password, $user->password)) {
            throw ValidationException::withMessages([
                'username' => ['用户名或密码错误'],
            ]);
        }

        if (! $user->isActive()) {
            throw ValidationException::withMessages([
                'username' => ['账号已被禁用，请联系管理员'],
            ]);
        }

        // 更新最后登录信息
        $user->update([
            'last_login_at' => now(),
            'last_login_ip' => $request->ip(),
        ]);

        \App\Models\OperationLog::log('user', 'login', "{$user->real_name} 登录系统");

        // 创建 Sanctum Token
        $token = $user->createToken('tradedoc')->plainTextToken;

        // 加载角色和权限
        $user->load(['roles', 'department']);
        $permissions = $user->getAllPermissions()->pluck('name');

        return response()->json([
            'data' => [
                'token' => $token,
                'user' => [
                    'id' => $user->id,
                    'username' => $user->username,
                    'real_name' => $user->real_name,
                    'email' => $user->email,
                    'phone' => $user->phone,
                    'department' => $user->department?->name,
                    'avatar' => $user->avatar,
                    'roles' => $user->roles->map(fn ($r) => [
                        'name' => $r->name,
                        'display_name' => $r->display_name ?? $r->name,
                    ]),
                    'permissions' => $permissions,
                ],
            ],
        ]);
    }

    public function me(Request $request): JsonResponse
    {
        $user = $request->user();
        $user->load(['roles', 'department']);
        $permissions = $user->getAllPermissions()->pluck('name');

        return response()->json([
            'data' => [
                'id' => $user->id,
                'username' => $user->username,
                'real_name' => $user->real_name,
                'email' => $user->email,
                'phone' => $user->phone,
                'department' => $user->department?->name,
                'avatar' => $user->avatar,
                'roles' => $user->roles->map(fn ($r) => [
                    'name' => $r->name,
                    'display_name' => $r->display_name ?? $r->name,
                ]),
                'permissions' => $permissions,
            ],
        ]);
    }

    public function logout(Request $request): JsonResponse
    {
        $request->user()->currentAccessToken()->delete();

        return response()->json(['message' => '已退出登录']);
    }
}
