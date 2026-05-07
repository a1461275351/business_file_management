<?php

declare(strict_types=1);

namespace App\Exports;

use App\Models\Document;
use Illuminate\Support\Collection;
use Maatwebsite\Excel\Concerns\FromCollection;
use Maatwebsite\Excel\Concerns\WithHeadings;
use Maatwebsite\Excel\Concerns\WithMapping;
use Maatwebsite\Excel\Concerns\WithStyles;
use PhpOffice\PhpSpreadsheet\Worksheet\Worksheet;

class DocumentsExport implements FromCollection, WithHeadings, WithMapping, WithStyles
{
    private array $ids;
    private array $filters;

    public function __construct(array $ids = [], array $filters = [])
    {
        $this->ids = $ids;
        $this->filters = $filters;
    }

    public function collection(): Collection
    {
        $query = Document::with(['documentType', 'uploader:id,real_name', 'order:id,order_no', 'customer:id,company_name', 'fields.template']);

        if (!empty($this->ids)) {
            $query->whereIn('id', $this->ids);
        } else {
            if (!empty($this->filters['document_type_id'])) {
                $query->where('document_type_id', $this->filters['document_type_id']);
            }
            if (!empty($this->filters['status'])) {
                $query->where('status', $this->filters['status']);
            }
            if (!empty($this->filters['date_from'])) {
                $query->where('created_at', '>=', $this->filters['date_from']);
            }
            if (!empty($this->filters['date_to'])) {
                $query->where('created_at', '<=', $this->filters['date_to'] . ' 23:59:59');
            }
        }

        return $query->orderByDesc('created_at')->get();
    }

    public function headings(): array
    {
        return [
            '文件编号', '文件类型', '文件名', '关联订单', '客户/供应商',
            '状态', '上传人', '上传时间',
            // 动态字段列（提取的业务字段）
            '报关单号/发票号', 'HS编码', '货物名称', '金额', '币种',
            '贸易方式', '运输方式', '目的国', '经营单位',
        ];
    }

    public function map($doc): array
    {
        $statusMap = [
            'draft' => '待处理', 'ocr_processing' => '识别中',
            'pending_review' => '待核对', 'pending_approval' => '待审批',
            'archived' => '已归档', 'voided' => '已作废',
        ];

        // 提取字段值
        $fieldMap = [];
        foreach ($doc->fields as $field) {
            $fieldMap[$field->field_key] = $field->field_value;
        }

        return [
            $doc->doc_no,
            $doc->documentType?->name ?? '',
            $doc->original_filename,
            $doc->order?->order_no ?? '',
            $doc->customer?->company_name ?? '',
            $statusMap[$doc->status] ?? $doc->status,
            $doc->uploader?->real_name ?? '',
            $doc->created_at?->format('Y-m-d H:i'),
            // 业务字段
            $fieldMap['declaration_no'] ?? $fieldMap['invoice_no'] ?? $fieldMap['bl_no'] ?? '',
            $fieldMap['hs_code'] ?? '',
            $fieldMap['goods_name'] ?? $fieldMap['goods_description'] ?? '',
            $fieldMap['trade_amount'] ?? $fieldMap['total_amount'] ?? $fieldMap['amount'] ?? '',
            $fieldMap['currency'] ?? '',
            $fieldMap['trade_mode'] ?? '',
            $fieldMap['transport_mode'] ?? '',
            $fieldMap['destination_country'] ?? '',
            $fieldMap['company_name'] ?? $fieldMap['seller'] ?? '',
        ];
    }

    public function styles(Worksheet $sheet): array
    {
        return [
            1 => ['font' => ['bold' => true, 'size' => 11]],
        ];
    }
}
