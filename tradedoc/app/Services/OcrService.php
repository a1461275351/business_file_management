<?php

declare(strict_types=1);

namespace App\Services;

use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;

class OcrService
{
    private string $baseUrl;

    public function __construct()
    {
        $this->baseUrl = config('services.python_ocr.url', 'http://127.0.0.1:8100');
    }

    /**
     * 触发 OCR 处理
     */
    public function processDocument(int $documentId, string $typeCode = ''): array
    {
        try {
            $response = Http::timeout(120)->post("{$this->baseUrl}/api/ocr/process", [
                'document_id' => $documentId,
                'file_path' => '',
                'document_type_code' => $typeCode,
                'language' => 'zh',
            ]);

            if ($response->successful()) {
                return $response->json();
            }

            Log::warning("OCR 处理失败", [
                'document_id' => $documentId,
                'status' => $response->status(),
                'body' => $response->body(),
            ]);

            return ['success' => false, 'error' => $response->json('detail', 'OCR 服务返回错误')];
        } catch (\Exception $e) {
            Log::error("OCR 服务调用异常", [
                'document_id' => $documentId,
                'error' => $e->getMessage(),
            ]);

            return ['success' => false, 'error' => '无法连接 OCR 服务: ' . $e->getMessage()];
        }
    }

    /**
     * 检查 OCR 服务健康状态
     */
    public function healthCheck(): array
    {
        try {
            $response = Http::timeout(5)->get("{$this->baseUrl}/api/health");
            return $response->json();
        } catch (\Exception $e) {
            return ['status' => 'offline', 'error' => $e->getMessage()];
        }
    }
}
