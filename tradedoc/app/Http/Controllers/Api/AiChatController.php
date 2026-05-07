<?php

declare(strict_types=1);

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\Document;
use App\Models\DocumentField;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Http;

class AiChatController extends Controller
{
    public function chat(Request $request): JsonResponse
    {
        $request->validate([
            'message' => 'required|string|max:2000',
        ]);

        $message = $request->message;
        $apiKey = config('services.dashscope.api_key', env('DASHSCOPE_API_KEY', ''));

        // 收集系统数据作为上下文
        $context = $this->buildContext();

        if ($apiKey) {
            // 有 API Key → 调通义千问
            $reply = $this->askQwen($message, $context, $apiKey);
        } else {
            // 无 API Key → 本地规则回答
            $reply = $this->localAnswer($message, $context);
        }

        return response()->json([
            'data' => ['reply' => $reply],
        ]);
    }

    private function buildContext(): string
    {
        $totalDocs = Document::count();
        $thisMonth = Document::whereMonth('created_at', now()->month)->count();
        $pending = Document::whereIn('status', ['draft', 'ocr_processing', 'pending_review', 'pending_approval'])->count();
        $archived = Document::where('status', 'archived')->count();

        $typeStats = DB::table('documents')
            ->join('document_types', 'documents.document_type_id', '=', 'document_types.id')
            ->whereNull('documents.deleted_at')
            ->select('document_types.name', DB::raw('count(*) as cnt'))
            ->groupBy('document_types.name')
            ->get()
            ->map(fn ($r) => "{$r->name}: {$r->cnt}份")
            ->join(', ');

        $recentFields = DB::table('document_fields')
            ->join('documents', 'document_fields.document_id', '=', 'documents.id')
            ->whereNotNull('document_fields.field_value')
            ->where('document_fields.field_value', '!=', '')
            ->select('documents.doc_no', 'document_fields.field_key', 'document_fields.field_value')
            ->orderByDesc('document_fields.id')
            ->limit(20)
            ->get()
            ->map(fn ($r) => "{$r->doc_no}: {$r->field_key}={$r->field_value}")
            ->join("\n");

        return "你是外贸业务文档管理系统的AI助手。以下是当前系统数据：\n"
            . "文件总数: {$totalDocs}, 本月: {$thisMonth}, 待处理: {$pending}, 已归档: {$archived}\n"
            . "文件类型分布: {$typeStats}\n"
            . "最近提取的字段:\n{$recentFields}";
    }

    private function askQwen(string $message, string $context, string $apiKey): string
    {
        try {
            $response = Http::timeout(30)
                ->withHeaders(['Authorization' => "Bearer {$apiKey}"])
                ->post('https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions', [
                    'model' => 'qwen-plus',
                    'messages' => [
                        ['role' => 'system', 'content' => $context],
                        ['role' => 'user', 'content' => $message],
                    ],
                    'temperature' => 0.7,
                    'max_tokens' => 1000,
                ]);

            if ($response->successful()) {
                return $response->json('choices.0.message.content', '抱歉，无法生成回答。');
            }

            return '大模型服务暂时不可用，请稍后重试。';
        } catch (\Exception $e) {
            return '连接大模型服务失败: ' . $e->getMessage();
        }
    }

    private function localAnswer(string $message, string $context): string
    {
        $totalDocs = Document::count();
        $thisMonth = Document::whereMonth('created_at', now()->month)->count();
        $pending = Document::whereIn('status', ['draft', 'ocr_processing', 'pending_review', 'pending_approval'])->count();

        if (str_contains($message, '多少') || str_contains($message, '统计')) {
            return "根据系统数据：\n\n**文件总数**: {$totalDocs} 份\n**本月上传**: {$thisMonth} 份\n**待处理**: {$pending} 份";
        }

        if (str_contains($message, '未归档') || str_contains($message, '待处理')) {
            return "当前有 **{$pending}** 份文件待处理。\n\n请到「文件管理」页面查看具体列表。";
        }

        return "当前系统共有 **{$totalDocs}** 份文件，其中 **{$pending}** 份待处理。\n\n_提示：配置阿里云 API Key 后可启用 AI 智能问答。_";
    }
}
