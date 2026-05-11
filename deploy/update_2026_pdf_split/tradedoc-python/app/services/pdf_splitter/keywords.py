"""文件类型关键词字典

每个文件类型对应一组关键词（中英文），命中阈值 MIN_HITS 视为该类型。
关键词来源：实际外贸单证样本，覆盖中英文双语单据。

匹配策略：
  - 不区分大小写
  - 任意命中 MIN_HITS 个不同关键词即判定为该类型
  - 多类型同时命中时，按命中数最高者；并列时按 TYPE_PRIORITY 排序
"""

# 每类至少命中几个关键词才认定（防止误判）
MIN_HITS = 2

# 文件类型关键词字典
# key = document_types.code（与数据库一致）
TYPE_KEYWORDS = {
    "customs_declaration": [
        # 中文
        "中华人民共和国海关",
        "出口货物报关单",
        "进口货物报关单",
        "报关单号",
        "预录入编号",
        "申报日期",
        "经营单位",
        "收发货人",
        "运抵国",
        "境内货源地",
        "贸易方式",
        "监管方式",
        "成交方式",
        "运输方式",
        "提运单号",
        "海关编码",
        "商品编号",
        # 英文（出口报关也有英文版）
        "Customs Declaration",
        "Declaration No",
    ],

    "commercial_invoice": [
        # 英文（商业发票一般以英文为主）
        "Commercial Invoice",
        "Invoice No",
        "Invoice Date",
        "Bill To",
        "Ship To",
        "Sold To",
        "Total Amount",
        "Unit Price",
        "Description of Goods",
        "Payment Terms",
        # 中文
        "商业发票",
        "发票号",
        "开票日期",
        "买方",
        "卖方",
        "付款条件",
    ],

    "packing_list": [
        # 英文
        "Packing List",
        "Gross Weight",
        "Net Weight",
        "N.W.",
        "G.W.",
        "Cartons",
        "CTNS",
        "CBM",
        "Measurement",
        "Total Packages",
        # 中文
        "装箱单",
        "毛重",
        "净重",
        "件数",
        "体积",
        "包装",
    ],

    "bank_receipt": [
        # 中文
        "银行水单",
        "汇款",
        "水单",
        "电汇凭证",
        "进账单",
        "汇入汇款",
        "汇出汇款",
        "结汇水单",
        # 英文
        "Remittance",
        "Wire Transfer",
        "Telegraphic Transfer",
        "TT Copy",
        "Bank Slip",
        "Payment Advice",
        "SWIFT",
    ],

    "bill_of_lading": [
        # 英文（提单多为英文）
        "Bill of Lading",
        "B/L No",
        "BL No",
        "Vessel",
        "Voyage No",
        "Carrier",
        "Port of Loading",
        "Port of Discharge",
        "Place of Receipt",
        "Place of Delivery",
        "Shipper",
        "Consignee",
        "Notify Party",
        "Container No",
        # 中文
        "提单",
        "运单",
        "船公司",
        "装货港",
        "卸货港",
        "发货人",
        "收货人",
    ],

    "certificate_of_origin": [
        # 英文
        "Certificate of Origin",
        "Form A",
        "Form B",
        "Form E",
        "Form F",
        "Country of Origin",
        "Exporter",
        "Producer",
        "GSP",
        "FTA",
        "CCPIT",
        # 中文
        "原产地证",
        "原产地证明书",
        "原产国",
        "出口商",
        "生产商",
    ],

    "contract": [
        # 英文
        "Sales Contract",
        "Purchase Contract",
        "Sales Agreement",
        "Purchase Agreement",
        "Contract No",
        "Buyer:",
        "Seller:",
        "Terms and Conditions",
        "Force Majeure",
        "Arbitration",
        # 中文
        "销售合同",
        "采购合同",
        "购销合同",
        "合同编号",
        "合同号",
        "甲方",
        "乙方",
        "争议解决",
        "不可抗力",
    ],

    "letter_of_credit": [
        # 英文
        "Letter of Credit",
        "Documentary Credit",
        "Irrevocable",
        "L/C No",
        "LC No",
        "Credit Number",
        "Applicant",
        "Beneficiary",
        "Issuing Bank",
        "Advising Bank",
        "Confirmation",
        "Available With",
        "UCP 600",
        # 中文
        "信用证",
        "开证行",
        "申请人",
        "受益人",
        "通知行",
    ],
}

# 同分时按优先级判定（数字越小优先级越高）
# 优先级原则：信息密集、独特性高的优先
TYPE_PRIORITY = {
    "customs_declaration": 1,   # 报关单格式最固定，关键词最准
    "letter_of_credit": 2,
    "bill_of_lading": 3,
    "certificate_of_origin": 4,
    "commercial_invoice": 5,
    "packing_list": 6,
    "bank_receipt": 7,
    "contract": 8,              # 合同关键词宽泛，最后判定
}


def normalize(text: str) -> str:
    """规范化文本: 去多余空白、转小写以便不区分大小写匹配"""
    if not text:
        return ""
    # 保留原大小写用于中文匹配，另外提供小写版本用于英文匹配
    return text


def count_hits(page_text: str, keywords: list[str]) -> tuple[int, list[str]]:
    """统计页面文字中命中了多少不同关键词

    Returns:
        (命中数, 命中的关键词列表)
    """
    if not page_text:
        return 0, []

    text_upper = page_text.upper()
    hits = []
    for kw in keywords:
        if kw.upper() in text_upper:
            hits.append(kw)
    return len(hits), hits
