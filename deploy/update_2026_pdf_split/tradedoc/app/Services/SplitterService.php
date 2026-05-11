<?php

declare(strict_types=1);

namespace App\Services;

use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;

class SplitterService
{
    private string $baseUrl;

    public function __construct()
    {
        $this->baseUrl = config('services.python_ocr.url', 'http://127.0.0.1:8100');
    }

    /**
     * 调 Python /api/splitter/analyze
     *
     * @return array{success: bool, data?: array, error?: string}
     */
    public function analyze(string $filePath): array
    {
        try {
            $response = Http::timeout(30)->post("{$this->baseUrl}/api/splitter/analyze", [
                'file_path' => $filePath,
            ]);

            if ($response->successful()) {
                return ['success' => true, 'data' => $response->json()];
            }

            return [
                'success' => false,
                'error' => $response->json('detail') ?? 'Python 服务返回 ' . $response->status(),
            ];
        } catch (\Throwable $e) {
            Log::error('PDF 拆分分析调用失败', ['file' => $filePath, 'error' => $e->getMessage()]);
            return ['success' => false, 'error' => '无法连接 Python 服务: ' . $e->getMessage()];
        }
    }

    /**
     * 调 Python /api/splitter/execute
     *
     * @param array $segments [{type_code, page_start, page_end, output_filename}, ...]
     * @return array{success: bool, results?: array, errors?: array, error?: string}
     */
    public function execute(string $sourcePdf, string $outputDir, array $segments): array
    {
        try {
            $response = Http::timeout(60)->post("{$this->baseUrl}/api/splitter/execute", [
                'source_pdf' => $sourcePdf,
                'output_dir' => $outputDir,
                'segments' => $segments,
            ]);

            if ($response->successful()) {
                return $response->json();
            }

            return [
                'success' => false,
                'error' => $response->json('detail') ?? 'Python 服务返回 ' . $response->status(),
            ];
        } catch (\Throwable $e) {
            Log::error('PDF 拆分执行调用失败', [
                'source' => $sourcePdf,
                'segments' => count($segments),
                'error' => $e->getMessage(),
            ]);
            return ['success' => false, 'error' => '无法连接 Python 服务: ' . $e->getMessage()];
        }
    }
}
