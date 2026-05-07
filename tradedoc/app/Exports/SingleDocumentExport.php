<?php

declare(strict_types=1);

namespace App\Exports;

use App\Models\Document;
use Maatwebsite\Excel\Concerns\FromArray;
use Maatwebsite\Excel\Concerns\WithHeadings;
use Maatwebsite\Excel\Concerns\WithStyles;
use Maatwebsite\Excel\Concerns\WithTitle;
use PhpOffice\PhpSpreadsheet\Worksheet\Worksheet;

class SingleDocumentExport implements FromArray, WithHeadings, WithStyles, WithTitle
{
    private Document $document;

    public function __construct(Document $document)
    {
        $this->document = $document;
    }

    public function title(): string
    {
        return $this->document->doc_no;
    }

    public function headings(): array
    {
        return ['字段名称', '字段标识', '字段值', '置信度', '提取方式', '是否已确认'];
    }

    public function array(): array
    {
        $this->document->load('fields.template');

        $methodMap = ['auto_ocr' => 'AI图片识别', 'auto_nlp' => 'AI文字解析', 'manual' => '人工录入', 'inferred' => '自动推断'];

        $rows = [];
        foreach ($this->document->fields as $field) {
            $rows[] = [
                $field->template?->field_name ?? $field->field_key,
                $field->field_key,
                $field->field_value ?? '',
                $field->confidence ? $field->confidence . '%' : '',
                $methodMap[$field->extract_method] ?? $field->extract_method,
                $field->is_confirmed ? '是' : '否',
            ];
        }

        // 加一行空行后添加基本信息
        $rows[] = [];
        $rows[] = ['--- 文件基本信息 ---', '', '', '', '', ''];
        $rows[] = ['文件编号', '', $this->document->doc_no, '', '', ''];
        $rows[] = ['文件类型', '', $this->document->documentType?->name ?? '', '', '', ''];
        $rows[] = ['原始文件名', '', $this->document->original_filename, '', '', ''];
        $rows[] = ['上传时间', '', $this->document->created_at?->format('Y-m-d H:i:s'), '', '', ''];
        $rows[] = ['状态', '', $this->document->status, '', '', ''];

        return $rows;
    }

    public function styles(Worksheet $sheet): array
    {
        return [
            1 => ['font' => ['bold' => true]],
        ];
    }
}
