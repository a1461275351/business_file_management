<?php

declare(strict_types=1);

use Illuminate\Support\Facades\Route;

// 所有前端路由走 SPA（排除 api 前缀）
Route::get('/{any}', fn () => view('app'))->where('any', '^(?!api).*$');
